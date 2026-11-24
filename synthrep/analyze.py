"""Compare estimates on synthetic data with the same estimates on the real data.

Per (dataset, synthesizer, replicate, coefficient):
  overlap    : CI overlap (Karr et al. 2006): mean share of each 95% CI covered by the intersection, 0 if disjoint
  zbias      : (b_syn - b_real) / se_real
  sign_ok    : same sign
  sig_ok     : same verdict at p<.05 (and same sign when both significant)
  covers     : real estimate lies inside the synthetic 95% CI (what a user of the synthetic file would conclude)
  se_ratio   : se_syn / se_real
  failed     : the analysis could not be run (category vanished, too few rows, ...)
Bootstrap resamples of the real data give the reference level expected from sampling noise alone.

  python -m synthrep.analyze
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
import pandas as pd

from .data import ROOT

ORDER = ["bootstrap", "cart", "copula", "tvae", "ctgan", "ctgan300", "marginals"]
TYPES = ["main", "nonlinear", "fe_adjusted", "trend", "interaction", "subgroup"]
Z = 1.959964


def metrics(df: pd.DataFrame, real: pd.DataFrame) -> pd.DataFrame:
    key = ["dataset", "model", "term"]
    m = df.merge(real[key + ["est", "se"]].rename(columns={"est": "est_r", "se": "se_r"}), on=key)
    lr, ur = m.est_r - Z * m.se_r, m.est_r + Z * m.se_r
    ls, us = m.est - Z * m.se, m.est + Z * m.se
    inter = (np.minimum(ur, us) - np.maximum(lr, ls)).clip(lower=0)
    m["failed"] = m.est.isna() | m.se.isna() | (m.se <= 0)
    m["overlap"] = 0.5 * (inter / (ur - lr) + inter / (us - ls))
    m["zbias"] = (m.est - m.est_r) / m.se_r
    m["sign_ok"] = np.sign(m.est) == np.sign(m.est_r)
    sig_r, sig_s = (m.est_r / m.se_r).abs() > Z, (m.est / m.se).abs() > Z
    m["sig_ok"] = (sig_r == sig_s) & (~(sig_r & sig_s) | m.sign_ok)
    m["covers"] = (m.est_r >= ls) & (m.est_r <= us)
    m["se_ratio"] = m.se / m.se_r
    # failed analyses count as non-replication
    for c in ["overlap"]:
        m.loc[m.failed, c] = 0.0
    for c in ["sign_ok", "sig_ok", "covers"]:
        m.loc[m.failed, c] = False
    return m


def pct(x):
    return f"{100 * x:.0f}%"


def table_by(m, rows, cols, val, fmt, agg="mean"):
    t = m.pivot_table(index=rows, columns=cols, values=val, aggfunc=agg)
    t = t.reindex(index=[r for r in ORDER if r in t.index]) if rows == "method" else t
    if cols == "type":
        t = t[[c for c in TYPES if c in t.columns]]
    return t.map(fmt)


def md(t: pd.DataFrame, first: str) -> list[str]:
    head = "| " + first + " | " + " | ".join(map(str, t.columns)) + " |"
    sep = "|---" * (len(t.columns) + 1) + "|"
    return [head, sep] + ["| " + str(i) + " | " + " | ".join(map(str, r)) + " |" for i, r in t.iterrows()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "synth_results"))
    a = ap.parse_args()
    d = pathlib.Path(a.dir)
    real = pd.DataFrame(map(json.loads, (d / "real.jsonl").read_text().splitlines()))
    est = pd.DataFrame(map(json.loads, (d / "estimates.jsonl").read_text().splitlines()))
    m = metrics(est, real)
    m.to_csv(d / "metrics.csv", index=False)

    reps = est.groupby("method").rep.nunique().reindex(ORDER).dropna().astype(int)
    L = ["# Can synthetic data replace the real thing? Pilot results", "",
         f"Real data: GSS 1972-2024 (n={int(real[real.dataset == 'gss'].n.max()):,}), "
         f"ACS 2022 Pennsylvania workers (n={int(real[real.dataset == 'acs'].n.max()):,}). "
         f"{real.groupby('dataset').size().sum()} published-style coefficients from "
         f"{real.groupby(['dataset', 'model']).ngroups} models.",
         "Replicates per synthesizer: " + ", ".join(f"{k} {v}" for k, v in reps.items()) +
         ". `bootstrap` = resampled real data (sampling-noise reference); `marginals` = no joint structure (floor).", ""]

    L += ["## 1. Headline: share of coefficients whose significance verdict matches the real data", ""]
    L += md(table_by(m, "method", "type", "sig_ok", pct), "synthesizer") + [""]
    L += ["## 2. Mean CI overlap with the real-data CI (1 = identical, 0 = disjoint)", ""]
    L += md(table_by(m, "method", "type", "overlap", lambda x: f"{x:.2f}"), "synthesizer") + [""]
    L += ["## 3. Share of synthetic 95% CIs that contain the real estimate", ""]
    L += md(table_by(m, "method", "type", "covers", pct), "synthesizer") + [""]
    L += ["## 4. Median |standardized bias| (in real-data SEs)", ""]
    m["abs_z"] = m.zbias.abs()
    L += md(table_by(m, "method", "type", "abs_z", lambda x: f"{x:.1f}", agg="median"), "synthesizer") + [""]

    L += ["## 5. Overall by synthesizer and dataset", "",
          "| synthesizer | dataset | sig. verdict match | CI overlap | real est. covered | sign match | median SE ratio | analyses failed | rows dropped (invalid values) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for meth in [x for x in ORDER if x in m.method.unique()]:
        for ds in ["gss", "acs"]:
            g = m[(m.method == meth) & (m.dataset == ds)]
            if not len(g):
                continue
            L.append(f"| {meth} | {ds} | {pct(g.sig_ok.mean())} | {g.overlap.mean():.2f} | {pct(g.covers.mean())} | "
                     f"{pct(g.sign_ok.mean())} | {g.se_ratio.median():.2f} | {pct(g.failed.mean())} | "
                     f"{pct(g.drop_duplicates(['rep']).dropped.mean())} |")

    # Combining m synthetic copies (Raab, Nowok & Dibben 2016). Under a correct synthesis model,
    # qbar_m - q_real ~ N(0, ubar/m), so z = (qbar_m - q_real) / sqrt(ubar/m) should exceed 1.96 in 5% of
    # coefficients. Larger rates mean the synthesizer distorts that coefficient beyond synthesis noise.
    ok = m[~m.failed]
    comb = ok.groupby(["dataset", "method", "model", "term", "type"]).agg(
        qbar=("est", "mean"), ubar=("se", lambda s: np.mean(s ** 2)), k=("est", "size"),
        est_r=("est_r", "first")).reset_index()
    comb["z"] = (comb.qbar - comb.est_r) / np.sqrt(comb.ubar / comb.k)
    comb["reject"] = comb.z.abs() > Z
    L += ["", "## 6. Pooling all synthetic copies (synthpop combining rule): share of coefficients where the",
          "pooled estimate differs from the real one beyond synthesis noise (|z| > 1.96; 5% expected if valid)", ""]
    L += md(table_by(comb, "method", "type", "reject", pct), "synthesizer") + [""]
    comb.to_csv(d / "combined.csv", index=False)

    L += ["", "## 7. Coefficient-level detail (mean CI overlap; real estimate and SE shown)", ""]
    det = m.pivot_table(index=["dataset", "model", "term", "type"], columns="method", values="overlap")
    det = det[[c for c in ORDER if c in det.columns]]
    r = real.set_index(["dataset", "model", "term"])
    L += ["| coefficient | type | real est (se) | " + " | ".join(det.columns) + " |",
          "|---|---|---|" + "---|" * len(det.columns)]
    for (ds, mod, term, typ), row in det.iterrows():
        rr = r.loc[(ds, mod, term)]
        desc = rr.desc
        L.append(f"| {ds}/{mod} {term} ({desc}) | {typ} | {rr.est:.3f} ({rr.se:.3f}) | " +
                 " | ".join(f"{v:.2f}" for v in row.values) + " |")
    (d / "summary.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
