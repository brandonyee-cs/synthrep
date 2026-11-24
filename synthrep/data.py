"""Build the two real analytic tables that synthesizers are trained on.

  GSS  (sociology): General Social Survey cumulative file 1972-2024, complete cases on core variables.
  ACS  (economics): 2022 ACS 1-year PUMS, Pennsylvania, employed wage earners aged 25-64.

Only RAW variables go into the synthesizers; derived variables (logs, squares, dummies, cohort)
are computed afterwards, the way a researcher using a released synthetic file would.

  python -m synthrep.data
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
import pyreadstat

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW_GSS_DIR = ROOT / "data/raw_gss"  # pilot used GSS cumulative 1972-2024, release R3a (gss7224_r3a.dta)
RAW_ACS = ROOT / "data/raw_acs/psam_p42.csv"
OUT = ROOT / "data"

# column -> "cat" (categorical) or "num" (numeric). Shared with the synthesizers.
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

# ACS 2018+ occupation codes -> 23 SOC major groups
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
    # years of schooling from SCHL (1-24)
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
    df = pd.read_pickle(OUT / f"{name}.pkl")
    return df


def main():
    for name, f in [("gss", build_gss), ("acs", build_acs)]:
        df = f()
        df.to_pickle(OUT / f"{name}.pkl")
        print(name, df.shape)
        print(df.head(3).to_string())


if __name__ == "__main__":
    main()
