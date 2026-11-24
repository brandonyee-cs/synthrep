"""Synthesizers. All are non-text generative models (no LLMs) and run on CPU.

  bootstrap  : resample real rows with replacement (reference: pure sampling noise, NOT a synthesizer)
  marginals  : each column drawn independently from its real marginal (floor: no joint structure)
  cart       : sequential CART synthesis, synthpop-style (the method most used by statistical agencies)
  copula     : Gaussian copula (SDV)
  ctgan      : conditional tabular GAN (SDV)
  tvae       : tabular variational autoencoder (SDV)

Each returns a synthetic DataFrame with the same columns and number of rows as the input.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from .data import SCHEMA


def bootstrap(df, schema, seed, **_):
    return df.sample(len(df), replace=True, random_state=seed).reset_index(drop=True)


def marginals(df, schema, seed, **_):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({c: rng.choice(df[c].values, len(df)) for c in df.columns})


def cart(df, schema, seed, min_leaf=5, **_):
    """Sequential CART (Reiter 2005; synthpop's default). Column j is synthesized from a tree fit on
    columns 1..j-1 of the real data; each synthetic row drops down the tree and takes a random real
    value from its leaf. Categorical predictors are ordinal-coded (an approximation to rpart's
    native factor splits)."""
    rng = np.random.default_rng(seed)
    cols = list(df.columns)
    n = len(df)
    codes = {c: pd.Categorical(df[c]) for c in cols if schema[c] == "cat"}
    real_X = pd.DataFrame({c: codes[c].codes if c in codes else df[c].values for c in cols})
    syn = pd.DataFrame(index=range(n))
    syn_X = pd.DataFrame(index=range(n))
    first = cols[0]
    idx = rng.integers(0, n, n)
    syn[first] = df[first].values[idx]
    syn_X[first] = real_X[first].values[idx]
    for j, c in enumerate(cols[1:], 1):
        pred = cols[:j]
        Tree = DecisionTreeClassifier if schema[c] == "cat" else DecisionTreeRegressor
        tree = Tree(min_samples_leaf=min_leaf, random_state=seed).fit(real_X[pred].values, real_X[c].values)
        leaf_real = tree.apply(real_X[pred].values)
        leaf_syn = tree.apply(syn_X[pred].values)
        donors = pd.Series(np.arange(n)).groupby(leaf_real).apply(np.asarray).to_dict()
        pick = np.empty(n, dtype=np.int64)
        for leaf in np.unique(leaf_syn):
            rows = np.where(leaf_syn == leaf)[0]
            pick[rows] = rng.choice(donors[leaf], len(rows))
        syn[c] = df[c].values[pick]
        syn_X[c] = real_X[c].values[pick]
    return syn[cols]


def _sdv(kind, df, schema, seed, epochs=300, **_):
    import torch
    from sdv.metadata import Metadata
    from sdv.single_table import CTGANSynthesizer, GaussianCopulaSynthesizer, TVAESynthesizer

    torch.manual_seed(seed)
    np.random.seed(seed)
    md = Metadata.detect_from_dataframes({"t": df}, infer_keys=None)
    for c, t in schema.items():
        md.update_column(c, table_name="t", sdtype="categorical" if t == "cat" else "numerical")
    if kind == "copula":
        m = GaussianCopulaSynthesizer(md, default_distribution="truncnorm")
    elif kind == "ctgan":
        m = CTGANSynthesizer(md, epochs=epochs, enable_gpu=False)
    else:
        m = TVAESynthesizer(md, epochs=epochs, enable_gpu=False)
    m.fit({"t": df})
    out = m.sample(len(df))
    if isinstance(out, dict):
        out = out["t"]
    return out[list(df.columns)]


def copula(df, schema, seed, **kw):
    return _sdv("copula", df, schema, seed, **kw)


def ctgan(df, schema, seed, **kw):
    return _sdv("ctgan", df, schema, seed, **kw)


def tvae(df, schema, seed, **kw):
    return _sdv("tvae", df, schema, seed, **kw)


SYNTHESIZERS = {"bootstrap": bootstrap, "marginals": marginals, "cart": cart,
                "copula": copula, "ctgan": ctgan, "tvae": tvae, "ctgan300": ctgan}


def synthesize(method, name, df, seed, **kw):
    return SYNTHESIZERS[method](df, SCHEMA[name], seed, **kw)
