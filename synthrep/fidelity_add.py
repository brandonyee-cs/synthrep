import sys

import pandas as pd

from .data import SCHEMA, load
from .fidelity import D, pmse_ratio, sdv_quality


def main(methods):
    m = pd.read_csv(D / "metrics.csv")
    t = pd.read_csv(D / "fidelity.csv")
    t = t[~t.method.isin(methods)]
    rows = []
    for name in ["gss", "acs"]:
        real = load(name)
        for meth in methods:
            f = D / "samples" / f"{name}_{meth}_rep0.pkl"
            if not f.exists():
                continue
            syn = pd.read_pickle(f)
            for col, typ in SCHEMA[name].items():
                syn[col] = syn[col].astype(str) if typ == "cat" else syn[col].astype(float)
            g = m[(m.dataset == name) & (m.method == meth)]
            rows.append(dict(dataset=name, method=meth, sdv_quality=sdv_quality(real, syn, SCHEMA[name]),
                             pmse_ratio=pmse_ratio(real, syn, SCHEMA[name]), ci_overlap=g.overlap.mean(),
                             covers=g.covers.mean(), sig_ok=g.sig_ok.mean()))
            print(rows[-1], flush=True)
    pd.concat([t, pd.DataFrame(rows)]).to_csv(D / "fidelity.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1:])
