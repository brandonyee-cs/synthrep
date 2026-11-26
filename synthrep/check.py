import argparse
import json

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.tree import DecisionTreeClassifier

Z = 1.959964


def fit(df, spec):
    out = {}
    for s in spec:
        w = s.get("weights")
        model = smf.wls(s["formula"], df, weights=df[w]) if w else smf.ols(s["formula"], df)
        r = model.fit(cov_type="HC1")
        for t in s["terms"]:
            out[(s["formula"], t)] = (float(r.params.get(t, np.nan)), float(r.bse.get(t, np.nan)))
    return out


def pmse_ratio(original, synthetic, seed=0, n_perm=5):
    both = pd.concat([original, synthetic], ignore_index=True)
    X = np.column_stack([pd.Categorical(both[c]).codes if both[c].dtype == object else both[c].values
                         for c in original.columns])
    y = np.r_[np.zeros(len(original)), np.ones(len(synthetic))]
    c = len(synthetic) / len(both)

    def pmse(labels):
        p = DecisionTreeClassifier(min_samples_leaf=100, max_depth=8, random_state=seed).fit(X, labels)
        return np.mean((p.predict_proba(X)[:, 1] - c) ** 2)

    rng = np.random.default_rng(seed)
    return pmse(y) / np.mean([pmse(rng.permutation(y)) for _ in range(n_perm)])


def check(original, synthetic, spec):
    orig = fit(original, spec)
    syn = [fit(s, spec) for s in synthetic]
    rows = []
    for key, (b, se) in orig.items():
        est = np.array([s[key][0] for s in syn])
        ses = np.array([s[key][1] for s in syn])
        qbar, ubar = np.nanmean(est), np.nanmean(ses ** 2)
        rows.append(dict(formula=key[0], term=key[1], original=b, original_se=se, synthetic=qbar,
                         single_file_coverage=float(np.mean(np.abs(est - b) <= Z * ses)),
                         combined_covers=bool(abs(qbar - b) <= Z * np.sqrt(ubar / len(syn))),
                         within_10pct=bool(abs(qbar - b) <= 0.1 * abs(b))))
    files = [pmse_ratio(original, s) for s in synthetic]
    return pd.DataFrame(rows), files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("synthetic", nargs="+")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    original = pd.read_csv(a.original)
    synthetic = [pd.read_csv(f)[original.columns] for f in a.synthetic]
    table, files = check(original, synthetic, spec)
    pd.set_option("display.width", 160)
    print(table.round(3).to_string(index=False))
    print(f"\ncombined interval contains original: {table.combined_covers.mean():.0%} of coefficients;"
          f" within 10%: {table.within_10pct.mean():.0%}")
    print("pMSE ratio by file (1 = indistinguishable from the original):", [round(float(x), 2) for x in files])
    if a.out:
        table.to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
