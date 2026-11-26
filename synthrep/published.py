import argparse
import json
import subprocess
import tempfile

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.formula.api as smf

from . import llm
from .data import OUT, RAW_ACS, RAW_GSS_DIR, ROOT, SCHEMA, load, occ_group
from .extra import fix_types
from .synth import SYNTHESIZERS

PSCHEMA = {
    "goldin": {"sex": "cat", "rac1p": "cat", "agep": "num", "schl": "num", "occ": "cat",
               "wkhp": "num", "wkwn": "num", "wagp": "num", "pwgtp": "num"},
    "glaeser": {"den": "cat", "educ": "num", "attend": "num"},
    "sw": {"sex": "cat", "year": "num", "happy": "cat", "wtssall": "num"},
}
SCHEMA.update(PSCHEMA)
llm.CODEBOOK.update({
    "goldin": """American Community Survey 2022, Pennsylvania, full-time year-round workers aged 25-64 (35+ usual hours,
40+ weeks), one row per worker. sex: 1 male, 2 female. rac1p: race code (1 White alone, 2 Black alone,
3 American Indian alone, 4 Alaska Native alone, 5 American Indian and Alaska Native, 6 Asian alone,
7 Native Hawaiian or Pacific Islander alone, 8 some other race alone, 9 two or more races). agep: age in years.
schl: educational attainment code 1-24 (16 regular high school diploma, 19 some college, 20 associate's,
21 bachelor's, 22 master's, 23 professional degree, 24 doctorate). occ: occupation group. wkhp: usual hours worked
per week. wkwn: weeks worked in the past 12 months. wagp: wage and salary income in dollars. pwgtp: person weight.""",
    "glaeser": """General Social Survey, U.S. adults born 1946 or later, surveyed 1972-1998, one row per respondent.
den: religious group (bapt Baptist, meth Methodist, luth Lutheran, presb Presbyterian, epis Episcopal,
othprot other Protestant, nodenom nondenominational Protestant, cath Catholic, jew Jewish, none no religion, other).
educ: years of schooling (0-20). attend: religious attendance, 0 never ... 8 more than once a week.""",
    "sw": """General Social Survey, U.S. adults, 1972-2006, one row per respondent. sex: 1 male, 2 female.
year: survey year. happy: 1 very happy, 2 pretty happy, 3 not too happy. wtssall: survey weight.""",
})

PAPERS = {
    "goldin": "Goldin (2014) Table 1",
    "glaeser": "Glaeser & Sacerdote (2008) Table I",
    "sw": "Stevenson & Wolfers (2009) Table 1",
}


def build():
    raw = pd.read_csv(RAW_ACS, usecols=["AGEP", "SEX", "RAC1P", "SCHL", "WKHP", "WKWN", "WAGP", "OCCP", "ESR",
                                         "PWGTP", "ADJINC"])
    d = raw[raw.AGEP.between(25, 64) & ~raw.ESR.isin([4, 5]) & (raw.WKHP >= 35) & (raw.WKWN >= 40)
            & (raw.WAGP * raw.ADJINC / 1e6 > 1400 * 0.5 * 7.25)].dropna(subset=["OCCP", "SCHL"])
    g = pd.DataFrame({"sex": d.SEX.astype(int).astype(str), "rac1p": d.RAC1P.astype(int).astype(str),
                      "agep": d.AGEP.astype(float), "schl": d.SCHL.astype(float),
                      "occ": d.OCCP.astype(int).map(occ_group), "wkhp": d.WKHP.astype(float),
                      "wkwn": d.WKWN.astype(float), "wagp": d.WAGP.astype(float), "pwgtp": d.PWGTP.astype(float)})
    tabs = {"goldin": g.reset_index(drop=True)}
    f = sorted(RAW_GSS_DIR.rglob("gss*.dta"))[-1]
    df, _ = pyreadstat.read_dta(f, usecols=["year", "cohort", "attend", "educ", "relig", "denom", "happy", "sex",
                                            "sample", "spaneng", "wtssall"], encoding="latin1")
    df = df.apply(pd.to_numeric, errors="coerce")
    q = df[(df.year <= 1998) & (df.cohort >= 1946) & (df.cohort < 9000)].dropna(subset=["attend", "educ", "relig"])
    prot = q.denom.map({1: "bapt", 2: "meth", 3: "luth", 4: "presb", 5: "epis", 6: "othprot", 7: "nodenom"})
    den = np.where(q.relig == 1, prot.fillna("othprot"), q.relig.map({2: "cath", 3: "jew", 4: "none"}).fillna("other"))
    tabs["glaeser"] = pd.DataFrame({"den": den, "educ": q.educ.astype(float),
                                    "attend": q.attend.astype(float)}).reset_index(drop=True)
    s = df[(df.year <= 2006) & ~df["sample"].isin([4, 5, 7])]
    s = s[~((s.year == 2006) & (s.spaneng == 2))].dropna(subset=["happy", "sex", "wtssall"])
    tabs["sw"] = pd.DataFrame({"sex": s.sex.astype(int).astype(str), "year": s.year.astype(float),
                               "happy": s.happy.astype(int).astype(str),
                               "wtssall": s.wtssall.astype(float)}).reset_index(drop=True)
    (OUT / "csv").mkdir(exist_ok=True)
    for k, t in tabs.items():
        t.to_pickle(OUT / f"{k}.pkl")
        t.to_csv(OUT / "csv" / f"{k}.csv", index=False)
        print(k, t.shape)


def fit(name, d):
    out = []
    if name == "goldin":
        d = d[(d.wagp > 0) & (d.wkhp > 0) & (d.wkwn > 0) & (d.pwgtp > 0)].copy()
        d["ly"], d["f"], d["a"] = np.log(d.wagp), (d.sex == "2") * 1.0, d.agep / 10
        d["lh"], d["lw"] = np.log(d.wkhp), np.log(d.wkwn)
        base = "ly ~ f + a + I(a**2) + I(a**3) + I(a**4) + C(rac1p)"
        specs = [("basic", base), ("time", base + " + lh + lw"), ("educ", base + " + lh + lw + C(schl)"),
                 ("occ", base + " + lh + lw + C(schl) + C(occ)")]
        for lab, fm in specs:
            r = smf.wls(fm, d, weights=d.pwgtp).fit(cov_type="HC1")
            out.append((lab, "female", r.params["f"], r.bse["f"]))
    elif name == "glaeser":
        d = d.copy()
        z = lambda x: (x - x.mean()) / x.std()
        d["za"], d["ze"] = z(d.attend), z(d.educ)
        r = smf.ols("za ~ ze", d).fit()
        out.append(("col1", "education", r.params["ze"], r.bse["ze"]))
        r = smf.ols('za ~ ze + C(den, Treatment("othprot"))', d).fit()
        out.append(("col2", "education", r.params["ze"], r.bse["ze"]))
    else:
        d = d[d.wtssall > 0].copy()
        d["h"] = 4 - d.happy.astype(int)
        m = np.average(d.h, weights=d.wtssall)
        sd = np.sqrt(np.average((d.h - m) ** 2, weights=d.wtssall))
        d["hz"], d["f"], d["t"] = (d.h - m) / sd, (d.sex == "2") * 1.0, (d.year - 1972) / 100
        d["ft"], d["mt"] = d.f * d.t, (1 - d.f) * d.t
        r = smf.wls("hz ~ ft + mt + f", d, weights=d.wtssall).fit(
            cov_type="cluster", cov_kwds={"groups": d.year.round().astype(int)})
        for t, lab in [("ft", "female trend"), ("mt", "male trend"), ("f", "female")]:
            out.append(("col4", lab, r.params[t], r.bse[t]))
    return [dict(paper=name, spec=s, term=t, est=float(e), se=float(se)) for s, t, e, se in out]


def synthesize(name, method, rep):
    df = load(name)
    seed = 1000 * rep + 7
    if method == "synthpop":
        cats = ",".join(c for c, t in PSCHEMA[name].items() if t == "cat")
        with tempfile.TemporaryDirectory() as d:
            df.to_csv(f"{d}/in.csv", index=False)
            subprocess.run(["nice", "-n", "15", "Rscript", str(ROOT / "synthrep/r/synthpop_run.R"), f"{d}/in.csv",
                            f"{d}/out", "1", str(seed), cats], check=True, capture_output=True)
            syn = pd.read_csv(f"{d}/out_0.csv", dtype=str)
    elif method == "llm":
        syn, _ = llm.synthesize(name, seed)
    else:
        syn = SYNTHESIZERS[method](df, PSCHEMA[name], seed)
    syn = fix_types(name, syn[list(PSCHEMA[name])].copy())
    return syn


def run(methods, reps):
    path = ROOT / "synth_results/published.jsonl"
    done = set()
    if path.exists():
        done = {(r["paper"], r["method"], r["rep"]) for r in map(json.loads, path.read_text().splitlines())}
    with path.open("a") as f:
        for name in PSCHEMA:
            if (name, "original", 0) not in done:
                for r in fit(name, load(name)):
                    f.write(json.dumps(dict(r, method="original", rep=0)) + "\n")
            for m in methods:
                for k in range(reps):
                    if (name, m, k) in done:
                        continue
                    for r in fit(name, synthesize(name, m, k)):
                        f.write(json.dumps(dict(r, method=m, rep=k)) + "\n")
                    f.flush()
                    print(name, m, k, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--methods", default="bootstrap,marginals,synthpop,copula")
    ap.add_argument("--reps", type=int, default=10)
    a = ap.parse_args()
    build() if a.cmd == "build" else run(a.methods.split(","), a.reps)
