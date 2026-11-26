import argparse
import concurrent.futures as cf
import csv
import io
import json
import os
import pathlib
import sys
import time

import numpy as np
import pandas as pd

from .data import ROOT, SCHEMA, load

MODEL = "google/gemini-2.5-flash-lite"
K_SHOW, K_ASK = 40, 100

CODEBOOK = {
    "gss": """General Social Survey, U.S. adults, one row per respondent, years 1972-2024.
year: survey year. age: years (18-89). sex: 1 male, 2 female. race: 1 white, 2 black, 3 other.
region: census region 1-4. educ: years of schooling (0-20).
marital: 1 married, 2 widowed, 3 divorced, 4 separated, 5 never married. childs: number of children (0-8).
wrkstat: 1 full time, 2 part time, 3 temporarily not working, 4 unemployed, 5 retired, 6 in school, 7 keeping house, 8 other.
attend: religious attendance, 0 never ... 8 more than once a week. realinc: family income in constant 1986 dollars.
happy: 1 very happy, 2 pretty happy, 3 not too happy.""",
    "acs": """American Community Survey 2022, Pennsylvania, employed wage earners aged 25-64, one row per worker.
age: years. sex: 1 male, 2 female. race: white, black, hispanic, asian, other. native: 1 born in the U.S., 2 foreign born.
schl: years of schooling. mar: 1 married, 2 widowed, 3 divorced, 4 separated, 5 never married.
puma: Public Use Microdata Area code within Pennsylvania. cow: class of worker 1-8 (1 private for-profit, 2 private nonprofit,
3 local government, 4 state government, 5 federal government, 6 self-employed not incorporated, 7 self-employed incorporated, 8 unpaid family).
occ: occupation group. wkhp: usual hours worked per week. wagp: wage and salary income in the past 12 months, dollars.""",
}


def client():
    from openai import OpenAI
    key = os.environ.get("OPENROUTER_API_KEY") or pathlib.Path("~/.openrouter_key").expanduser().read_text().strip()
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)


def valid_codes(name):
    df = load(name)
    return "\n".join(f"Valid {c} codes: " + ", ".join(sorted(df[c].unique(), key=lambda v: (len(v), v)))
                     for c, t in SCHEMA[name].items() if t == "cat" and df[c].nunique() > 9)


def prompt(name, shown):
    buf = io.StringIO()
    shown.to_csv(buf, index=False, float_format="%.0f")
    return (f"{CODEBOOK[name]}\n{valid_codes(name)}\n\nHere are {len(shown)} rows drawn at random from the survey:\n\n{buf.getvalue()}\n"
            f"Write {K_ASK} new rows that could come from the same survey. They should follow the same joint "
            f"distribution as the full survey, not copy these rows. Use the same columns and codes. "
            f"Answer with CSV only: the header line and then {K_ASK} rows, with no other text.")


def parse(name, text, levels, ranges):
    cols = list(SCHEMA[name])
    text = text.strip().strip("`")
    if text.startswith("csv"):
        text = text[3:]
    rows = []
    for rec in csv.reader(io.StringIO(text.strip())):
        if len(rec) != len(cols) or rec[0].strip() == cols[0]:
            continue
        r = {}
        try:
            for c, v in zip(cols, rec):
                v = v.strip()
                if SCHEMA[name][c] == "cat":
                    if v.endswith(".0"):
                        v = v[:-2]
                    if v not in levels[c]:
                        raise ValueError
                    r[c] = v
                else:
                    x = float(v)
                    if not ranges[c][0] <= x <= ranges[c][1]:
                        raise ValueError
                    r[c] = x
        except ValueError:
            continue
        rows.append(r)
    return rows


def call(cl, name, shown):
    for wait in [2, 5, 15, 30, 60, 120, 0]:
        try:
            return _call(cl, name, shown)
        except Exception as e:
            if not wait:
                print("giving up on one request:", str(e)[:80], flush=True)
                return "", 0
            time.sleep(wait)


def _call(cl, name, shown):
    r = cl.chat.completions.create(model=MODEL, temperature=1.0, max_tokens=6000,
                                   messages=[{"role": "user", "content": prompt(name, shown)}],
                                   extra_body={"usage": {"include": True},
                                               "provider": {"order": ["google-ai-studio"], "allow_fallbacks": False}})
    cost = getattr(r, "usage", None)
    cost = getattr(cost, "cost", None) or (cost.model_extra or {}).get("cost", 0) if cost else 0
    return r.choices[0].message.content or "", cost or 0


def synthesize(name, seed, procs=int(os.environ.get("LLM_THREADS", 8)), log=None, df=None, tag=""):
    df = load(name) if df is None else df
    full = load(name)
    levels = {c: set(full[c].unique()) for c, t in SCHEMA[name].items() if t == "cat"}
    ranges = {c: (full[c].min(), full[c].max()) for c, t in SCHEMA[name].items() if t == "num"}
    cl = client()
    ck = ROOT / f"data/llm/{name}{tag}_seed{seed}.partial.json"
    out, asked, cost = json.loads(ck.read_text()) if ck.exists() else ([], 0, 0.0)
    rng = np.random.default_rng(seed + len(out))
    with cf.ThreadPoolExecutor(procs) as ex:
        while len(out) < len(df):
            need = min(120, int(np.ceil((len(df) - len(out)) / (0.7 * K_ASK))) + 2)
            shows = [df.iloc[rng.choice(len(df), K_SHOW, replace=False)] for _ in range(need)]
            for text, c in ex.map(lambda s: call(cl, name, s), shows):
                out += parse(name, text, levels, ranges)
                asked += K_ASK
                cost += c
            ck.write_text(json.dumps([out, asked, cost]))
            if log:
                print(f"  {name} seed {seed}: {len(out)}/{len(df)} rows, ${cost:.2f}", file=log, flush=True)
    syn = pd.DataFrame(out[:len(df)])[list(SCHEMA[name])]
    return syn, dict(asked=asked, kept=len(out), cost=round(cost, 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="gss")
    ap.add_argument("--rep", type=int, default=0)
    a = ap.parse_args()
    d = ROOT / "data/llm"
    d.mkdir(parents=True, exist_ok=True)
    syn, info = synthesize(a.dataset, 1000 * a.rep + 7, log=sys.stdout)
    syn.to_pickle(d / f"{a.dataset}_rep{a.rep}.pkl")
    (d / f"{a.dataset}_rep{a.rep}.json").write_text(json.dumps(info))
    print(info)


if __name__ == "__main__":
    main()
