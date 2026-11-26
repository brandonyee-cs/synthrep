import pathlib

import numpy as np
import pandas as pd
import pyreadstat

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW_GSS_DIR = ROOT / "data/raw_gss"
RAW_ACS = ROOT / "data/raw_acs/psam_p42.csv"
OUT = ROOT / "data"

SCHEMA = {
    "gss": {
        "year": "cat", "age": "num", "sex": "cat", "race": "cat", "region": "cat",
        "educ": "num", "marital": "cat", "childs": "num", "wrkstat": "cat",
        "attend": "num", "realinc": "num", "happy": "cat",
    },
    "acs": {
        "age": "num", "sex": "cat", "race": "cat", "native": "cat", "schl": "num",
        "mar": "cat", "puma": "cat", "cow": "cat", "occ": "cat", "wkhp": "num", "wagp": "num",
    },
}

OCC_BREAKS = [(10, "mgmt"), (500, "business"), (1005, "computer"), (1305, "engineering"),
              (1600, "science"), (2001, "community"), (2100, "legal"), (2205, "education"),
              (2600, "arts"), (3000, "health_pract"), (3601, "health_support"),
              (3700, "protective"), (4000, "food"), (4200, "cleaning"), (4330, "personal"),
              (4700, "sales"), (5000, "office"), (6005, "farm"), (6200, "construction"),
              (7000, "repair"), (7700, "production"), (9005, "transport"), (9800, "military")]


def occ_group(code: int) -> str:
    lab = OCC_BREAKS[0][1]
    for lo, name in OCC_BREAKS:
        if code >= lo:
            lab = name
    return lab


def build_gss() -> pd.DataFrame:
    cols = list(SCHEMA["gss"])
    found = sorted(RAW_GSS_DIR.rglob("gss*.dta"))
    if not found:
        raise FileNotFoundError("GSS .dta not found; run scripts/get_data.py")
    df, _ = pyreadstat.read_dta(found[-1], usecols=cols, encoding="latin1")
    df = df.dropna()
    df = df[df.realinc > 0]
    for c, t in SCHEMA["gss"].items():
        df[c] = df[c].astype(int).astype(str) if t == "cat" else df[c].astype(float)
    return df[list(SCHEMA['gss'])].reset_index(drop=True)


def build_acs() -> pd.DataFrame:
    raw = pd.read_csv(RAW_ACS, usecols=["AGEP", "SEX", "RAC1P", "HISP", "SCHL", "WAGP", "WKHP",
                                        "MAR", "OCCP", "PUMA", "COW", "NATIVITY", "ESR"])
    d = raw[(raw.AGEP.between(25, 64)) & (raw.WAGP > 0) & (raw.WKHP >= 1) & raw.ESR.isin([1, 2])]
    d = d.dropna(subset=["OCCP", "COW"])
    race = np.select([d.HISP > 1, d.RAC1P == 1, d.RAC1P == 2, d.RAC1P == 6],
                     ["hispanic", "white", "black", "asian"], "other")
    yrs = {**{k: 0 for k in range(1, 4)}, 4: 1, 5: 2, 6: 3, 7: 4, 8: 5, 9: 6, 10: 7, 11: 8,
           12: 9, 13: 10, 14: 11, 15: 12, 16: 12, 17: 12, 18: 13, 19: 13, 20: 14, 21: 16,
           22: 18, 23: 19, 24: 20}
    out = pd.DataFrame({
        "age": d.AGEP.astype(float), "sex": d.SEX.astype(int).astype(str), "race": race,
        "schl": d.SCHL.map(yrs).astype(float), "wagp": d.WAGP.astype(float),
        "wkhp": d.WKHP.astype(float), "mar": d.MAR.astype(int).astype(str),
        "occ": d.OCCP.astype(int).map(occ_group), "puma": d.PUMA.astype(int).astype(str),
        "cow": d.COW.astype(int).astype(str), "native": d.NATIVITY.astype(int).astype(str),
    })
    return out[list(SCHEMA['acs'])].reset_index(drop=True)


def load(name: str) -> pd.DataFrame:
    return pd.read_pickle(OUT / f"{name}.pkl")


def add_weights(name: str, df: pd.DataFrame) -> pd.DataFrame:
    if name == "gss":
        cols = list(SCHEMA["gss"])
        found = sorted(RAW_GSS_DIR.rglob("gss*.dta"))
        raw, _ = pyreadstat.read_dta(found[-1], usecols=cols + ["wtssps"], encoding="latin1")
        raw = raw.dropna(subset=cols)
        w = raw[raw.realinc > 0].wtssps.astype(float).values
    else:
        raw = pd.read_csv(RAW_ACS, usecols=["AGEP", "WAGP", "WKHP", "ESR", "OCCP", "COW", "PWGTP"])
        d = raw[(raw.AGEP.between(25, 64)) & (raw.WAGP > 0) & (raw.WKHP >= 1) & raw.ESR.isin([1, 2])]
        w = d.dropna(subset=["OCCP", "COW"]).PWGTP.astype(float).values
    out = df.copy()
    out["w"] = w
    return out


def main():
    (OUT / "csv").mkdir(parents=True, exist_ok=True)
    for name, f in [("gss", build_gss), ("acs", build_acs)]:
        df = f()
        df.to_pickle(OUT / f"{name}.pkl")
        df.to_csv(OUT / "csv" / f"{name}.csv", index=False)
        dw = add_weights(name, df)
        dw.to_pickle(OUT / f"{name}_w.pkl")
        dw.to_csv(OUT / "csv" / f"{name}w.csv", index=False)
        print(name, df.shape)
        print(df.head(3).to_string())


if __name__ == "__main__":
    main()
