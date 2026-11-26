import numpy as np
import pandas as pd

from .data import SCHEMA


def bootstrap(df, schema, seed, **_):
    return df.sample(len(df), replace=True, random_state=seed).reset_index(drop=True)


def marginals(df, schema, seed, **_):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({c: rng.choice(df[c].values, len(df)) for c in df.columns})


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


SYNTHESIZERS = {"bootstrap": bootstrap, "marginals": marginals,
                "copula": copula, "ctgan": ctgan, "tvae": tvae, "ctgan300": ctgan, "tvae300": tvae}


def synthesize(method, name, df, seed, **kw):
    return SYNTHESIZERS[method](df, SCHEMA[name], seed, **kw)
