import json
import sys

import pandas as pd

from .analyses import run_battery
from .data import ROOT, SCHEMA
from .synth import SYNTHESIZERS

D = ROOT / "synth_results"


def fix_types(name, syn):
    for c, t in SCHEMA[name].items():
        syn[c] = syn[c].astype(str).str.replace(r"\.0$", "", regex=True) if t == "cat" else syn[c].astype(float)
    return syn


def append(path, rows, keys):
    done = set()
    if path.exists():
        done = {tuple(r[k] for k in keys) for r in map(json.loads, path.read_text().splitlines())}
    new = [r for r in rows if tuple(r[k] for k in keys) not in done]
    with path.open("a") as f:
        for r in new:
            f.write(json.dumps(r) + "\n")
    return len(new)


def battery(name, syn, method, rep):
    rows = run_battery(name, syn)
    for r in rows:
        r.update(dataset=name, method=method, rep=rep)
    return rows


def from_files(method):
    rows = []
    for name in ["gss", "acs"]:
        if method == "synthpop":
            files = sorted((ROOT / "data/sp").glob(f"{name}_[0-9]*.csv"))
            reader = lambda f: pd.read_csv(f, dtype=str)
            rep_of = lambda f: int(f.stem.split("_")[-1])
        else:
            files = sorted((ROOT / "data/llm").glob(f"{name}_rep*.pkl"))
            reader = pd.read_pickle
            rep_of = lambda f: int(f.stem.split("rep")[-1])
        for f in files:
            syn = fix_types(name, reader(f))
            rows += battery(name, syn, method, rep_of(f))
            if rep_of(f) == 0:
                syn.to_pickle(D / "samples" / f"{name}_{method}_rep0.pkl")
    print(method, append(D / "estimates.jsonl", rows, ["dataset", "method", "rep", "model", "term"]), "rows added")


def weighted(reps=5):
    real_rows, rows = [], []
    for name in ["gss", "acs"]:
        df = pd.read_pickle(ROOT / f"data/{name}_w.pkl")
        real_rows += battery(name, df, "real", 0)
        for f in sorted((ROOT / "data/sp").glob(f"{name}w_[0-9]*.csv")):
            syn = fix_types(name, pd.read_csv(f, dtype=str))
            syn["w"] = syn.w.astype(float)
            rows += battery(name, syn, "synthpop", int(f.stem.split("_")[-1]))
        schema = {**SCHEMA[name], "w": "num"}
        for meth in ["bootstrap", "marginals", "copula"]:
            for k in range(reps):
                syn = SYNTHESIZERS[meth](df, schema, 1000 * k + 7)
                syn = fix_types(name, syn)
                syn["w"] = syn.w.astype(float).clip(lower=df.w.min())
                rows += battery(name, syn, meth, k)
                print(name, meth, k, flush=True)
    (D / "real_w.jsonl").write_text("".join(json.dumps(r) + "\n" for r in real_rows))
    print("weighted", append(D / "estimates_w.jsonl", rows, ["dataset", "method", "rep", "model", "term"]), "rows added")


if __name__ == "__main__":
    {"synthpop": lambda: from_files("synthpop"), "llm": lambda: from_files("llm"), "weighted": weighted}[sys.argv[1]]()
