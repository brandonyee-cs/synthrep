import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from .analyze import ORDER, md
from .data import ROOT, SCHEMA, load

D = ROOT / "synth_results"


def sdv_quality(real, syn, schema):
    from sdv.evaluation import evaluate_quality
    from sdv.metadata import Metadata
    md_ = Metadata.detect_from_dataframes({"t": real}, infer_keys=None)
    for c, t in schema.items():
        md_.update_column(c, table_name="t", sdtype="categorical" if t == "cat" else "numerical")
    try:
        rep = evaluate_quality({"t": real}, {"t": syn}, md_, verbose=False)
    except Exception:
        rep = evaluate_quality(real, syn, md_, verbose=False)
    return rep.get_score()


def pmse_ratio(real, syn, schema, seed=0, n_perm=5):
    both = pd.concat([real, syn], ignore_index=True)
    X = np.column_stack([pd.Categorical(both[c]).codes if schema[c] == "cat" else both[c].values
                         for c in real.columns])
    y = np.r_[np.zeros(len(real)), np.ones(len(syn))]
    c = len(syn) / len(both)

    def pmse(labels):
        clf = DecisionTreeClassifier(min_samples_leaf=100, max_depth=8, random_state=seed).fit(X, labels)
        p = clf.predict_proba(X)[:, 1]
        return np.mean((p - c) ** 2)

    rng = np.random.default_rng(seed)
    null = np.mean([pmse(rng.permutation(y)) for _ in range(n_perm)])
    return pmse(y) / null


def main():
    m = pd.read_csv(D / "metrics.csv")
    rows = []
    for name in ["gss", "acs"]:
        real = load(name)
        for meth in ORDER:
            f = D / "samples" / f"{name}_{meth}_rep0.pkl"
            if not f.exists():
                continue
            syn = pd.read_pickle(f)
            for col, t in SCHEMA[name].items():
                if t == "cat":
                    syn[col] = syn[col].astype(str)
            g = m[(m.dataset == name) & (m.method == meth)]
            rows.append(dict(dataset=name, method=meth,
                             sdv_quality=sdv_quality(real, syn, SCHEMA[name]),
                             pmse_ratio=pmse_ratio(real, syn, SCHEMA[name]),
                             ci_overlap=g.overlap.mean(), covers=g.covers.mean(), sig_ok=g.sig_ok.mean()))
            print(rows[-1], flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(D / "fidelity.csv", index=False)
    show = t.copy()
    show["sdv_quality"] = show.sdv_quality.map(lambda x: f"{100 * x:.0f}%")
    show["pmse_ratio"] = show.pmse_ratio.map(lambda x: f"{x:.1f}")
    show["ci_overlap"] = show.ci_overlap.map(lambda x: f"{x:.2f}")
    for c in ["covers", "sig_ok"]:
        show[c] = show[c].map(lambda x: f"{100 * x:.0f}%")
    show.index = show.dataset + " / " + show.method
    show = show.drop(columns=["dataset", "method"])
    corr = t[["sdv_quality", "pmse_ratio", "ci_overlap", "covers"]].corr(method="spearman")
    L = ["## Generic fidelity vs analysis-specific validity (replicate 0)", "",
         "`sdv_quality`: SDV Quality Report score (higher = 'better'). `pmse_ratio`: 1 = indistinguishable from real.", ""]
    L += md(show, "dataset / synthesizer")
    L += ["", f"Spearman rank correlation with mean CI overlap: SDV quality {corr.loc['sdv_quality', 'ci_overlap']:.2f}, "
               f"pMSE ratio {corr.loc['pmse_ratio', 'ci_overlap']:.2f} (n={len(t)} synthesizer-dataset files)."]
    (D / "fidelity.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
