"""Battery of published-style analyses. Each estimate is tagged with a coefficient TYPE, the
unit of the main comparison:

  main         : main-effect slope on a common variable (returns to schooling, gender gap)
  nonlinear    : curvature term (age^2, experience^2)
  interaction  : product term (female x education, Black x BA)
  trend        : time/cohort slope or time x group (declining female happiness)
  subgroup     : estimate within a subsample (gap among Asian workers; gap in the 2010s)
  fe_adjusted  : coefficient after high-cardinality fixed effects (occupation, PUMA, year)

All models are OLS (linear probability for binary outcomes) with HC1 robust SEs, unweighted.
Derived variables are computed from raw columns AFTER synthesis.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

# (model id, description, formula, subset function or None, {term: type})
GSS_MODELS = [
    ("G1", "Family-income function", "lninc ~ educ + age + age2 + female + black + other + married", None,
     {"educ": "main", "female": "main", "black": "main", "married": "main", "age2": "nonlinear"}),
    ("G2", "Gender x education in income", "lninc ~ educ * female + age + age2 + black + other", None,
     {"educ:female": "interaction"}),
    ("G3", "Correlates of happiness", "vhappy ~ married + lninc + attend + childs + age + female + black", None,
     {"married": "main", "lninc": "main", "attend": "main", "childs": "main"}),
    ("G4", "Declining female happiness (Stevenson & Wolfers 2009)",
     "vhappy ~ female * yr10 + age + age2 + black + other + married", None,
     {"yr10": "trend", "female:yr10": "trend"}),
    ("G5", "Black-white income gap, 2010+", "lninc ~ black + educ + age + age2",
     lambda d: d[(d.yr >= 2010) & d.race.isin(["1", "2"])], {"black": "subgroup"}),
    ("G6", "Black-white income gap, 1970s", "lninc ~ black + educ + age + age2",
     lambda d: d[(d.yr < 1980) & d.race.isin(["1", "2"])], {"black": "subgroup"}),
    ("G7", "Religious attendance by birth cohort", "attend ~ cohort10 + age + female + black", None,
     {"cohort10": "trend"}),
    ("G8", "Income function with region and year FE",
     "lninc ~ educ + female + age + age2 + C(region) + C(year)", None,
     {"educ": "fe_adjusted", "female": "fe_adjusted"}),
]

ACS_MODELS = [
    ("A1", "Mincer wage equation", "lnwage ~ schl + exp + exp2 + female + black + hispanic + asian + other + lnhrs",
     None, {"schl": "main", "female": "main", "black": "main", "lnhrs": "main", "exp2": "nonlinear"}),
    ("A2", "Gender gap with occupation FE", "lnwage ~ female + schl + exp + exp2 + lnhrs + C(occ)", None,
     {"female": "fe_adjusted", "schl": "fe_adjusted"}),
    ("A3", "Gender gap with occupation and PUMA FE",
     "lnwage ~ female + schl + exp + exp2 + lnhrs + C(occ) + C(puma)", None, {"female": "fe_adjusted"}),
    ("A4", "Return to BA by race", "lnwage ~ ba * black + exp + exp2 + female + lnhrs", None,
     {"ba:black": "interaction", "ba": "main"}),
    ("A5", "Marriage premium by sex", "lnwage ~ married * female + schl + exp + exp2 + lnhrs", None,
     {"married:female": "interaction", "married": "main"}),
    ("A6", "Gender gap among Asian workers", "lnwage ~ female + schl + exp + exp2 + lnhrs",
     lambda d: d[d.race == "asian"], {"female": "subgroup"}),
    ("A7", "Gender gap among Black workers", "lnwage ~ female + schl + exp + exp2 + lnhrs",
     lambda d: d[d.race == "black"], {"female": "subgroup"}),
    ("A8", "Immigrant wage gap", "lnwage ~ foreign + schl + exp + exp2 + female + lnhrs", None,
     {"foreign": "main"}),
]

MODELS = {"gss": GSS_MODELS, "acs": ACS_MODELS}


def derive(name: str, df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Compute derived variables. Returns (data, share of rows dropped as invalid, e.g. income <= 0)."""
    d = df.copy()
    n0 = len(d)
    if name == "gss":
        d = d[d.realinc > 0]
        d["yr"] = d.year.astype(int)
        d["yr10"] = (d.yr - 1972) / 10
        d["lninc"] = np.log(d.realinc)
        d["age2"] = d.age ** 2 / 100
        d["female"] = (d.sex == "2").astype(float)
        d["black"] = (d.race == "2").astype(float)
        d["other"] = (d.race == "3").astype(float)
        d["married"] = (d.marital == "1").astype(float)
        d["vhappy"] = (d.happy == "1").astype(float)
        d["cohort10"] = (d.yr - d.age - 1900) / 10
    else:
        d = d[(d.wagp > 0) & (d.wkhp > 0)]
        d["lnwage"] = np.log(d.wagp)
        d["lnhrs"] = np.log(d.wkhp)
        d["exp"] = (d.age - d.schl - 6).clip(lower=0)
        d["exp2"] = d.exp ** 2 / 100
        d["female"] = (d.sex == "2").astype(float)
        for r in ["black", "hispanic", "asian", "other"]:
            d[r] = (d.race == r).astype(float)
        d["ba"] = (d.schl >= 16).astype(float)
        d["married"] = (d.mar == "1").astype(float)
        d["foreign"] = (d.native == "2").astype(float)
    return d, 1 - len(d) / n0 if n0 else np.nan


def run_battery(name: str, df: pd.DataFrame) -> list[dict]:
    d, dropped = derive(name, df)
    out = []
    for mid, desc, f, sub, terms in MODELS[name]:
        dd = sub(d) if sub else d
        try:
            if len(dd) < 30:
                raise ValueError("too few rows")
            fit = smf.ols(f, data=dd).fit(cov_type="HC1")
            for t, typ in terms.items():
                ok = t in fit.params.index
                out.append(dict(model=mid, desc=desc, term=t, type=typ, n=len(dd), dropped=dropped,
                                est=float(fit.params[t]) if ok else np.nan,
                                se=float(fit.bse[t]) if ok else np.nan))
        except Exception as e:  # degenerate synthetic data (e.g. a category vanished)
            for t, typ in terms.items():
                out.append(dict(model=mid, desc=desc, term=t, type=typ, n=len(dd), dropped=dropped,
                                est=np.nan, se=np.nan, error=str(e)[:80]))
    return out
