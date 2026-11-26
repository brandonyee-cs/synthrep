import json

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.formula.api as smf

from .analyses import MODELS, derive
from .analyze import metrics
from .data import RAW_ACS, RAW_GSS_DIR, ROOT, SCHEMA

D = ROOT / "synth_results"
Z = 1.959964


def design_columns(name):
    if name == "gss":
        cols = list(SCHEMA["gss"])
        f = sorted(RAW_GSS_DIR.rglob("gss*.dta"))[-1]
        raw, _ = pyreadstat.read_dta(f, usecols=cols + ["vstrat", "vpsu"], encoding="latin1")
        raw = raw.dropna(subset=cols)
        raw = raw[raw.realinc > 0].reset_index(drop=True)
        own = pd.Series(np.arange(len(raw)) + 10**7, index=raw.index)
        cl = (raw.vstrat * 1000 + raw.vpsu).where(raw.vstrat.notna(), own)
        return pd.DataFrame({"cluster": cl.astype(np.int64).values})
    reps = [f"PWGTP{i}" for i in range(1, 81)]
    raw = pd.read_csv(RAW_ACS, usecols=["AGEP", "WAGP", "WKHP", "ESR", "OCCP", "COW"] + reps)
    d = raw[(raw.AGEP.between(25, 64)) & (raw.WAGP > 0) & (raw.WKHP >= 1) & raw.ESR.isin([1, 2])]
    return d.dropna(subset=["OCCP", "COW"])[reps].astype(float).reset_index(drop=True)


def design_se(name):
    df = pd.read_pickle(ROOT / f"data/{name}_w.pkl")
    df = pd.concat([df, design_columns(name)], axis=1)
    d, _ = derive(name, df)
    out = []
    for mid, desc, f, sub, terms in MODELS[name]:
        dd = sub(d) if sub else d
        dd = dd[dd.w > 0]
        if name == "gss":
            fit = smf.wls(f, data=dd, weights=dd.w).fit(cov_type="cluster", cov_kwds={"groups": dd.cluster})
            se = {t: float(fit.bse[t]) for t in terms}
        else:
            full = smf.wls(f, data=dd, weights=dd.w).fit()
            draws = np.array([[smf.wls(f, data=dd, weights=dd[f"PWGTP{i}"].clip(lower=0) + 1e-9).fit().params[t]
                               for t in terms] for i in range(1, 81)])
            base = np.array([full.params[t] for t in terms])
            se = dict(zip(terms, np.sqrt(4 / 80 * ((draws - base) ** 2).sum(0))))
        for t in terms:
            out.append(dict(dataset=name, model=mid, term=t, se_design=float(se[t])))
        print(name, mid, flush=True)
    return out


def main():
    rows = design_se("gss") + design_se("acs")
    des = pd.DataFrame(rows)
    real = pd.DataFrame(map(json.loads, (D / "real_w.jsonl").read_text().splitlines()))
    des = des.merge(real[["dataset", "model", "term", "se"]], on=["dataset", "model", "term"])
    des["deff"] = des.se_design / des.se
    des.to_csv(D / "design_se.csv", index=False)
    est = pd.DataFrame(map(json.loads, (D / "estimates_w.jsonl").read_text().splitlines()))
    m = metrics(est, real).merge(des[["dataset", "model", "term", "deff", "se_design"]],
                                 on=["dataset", "model", "term"])
    m["covers_design"] = (m.est - m.est_r).abs() <= Z * m.se * m.deff
    summary = m.groupby("method")[["covers", "covers_design"]].mean()
    print("median design effect on SEs:", des.groupby("dataset").deff.median().round(2).to_dict())
    print(summary.round(2))
    summary.to_csv(D / "design_coverage.csv")


if __name__ == "__main__":
    main()
