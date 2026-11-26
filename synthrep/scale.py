import argparse
import concurrent.futures as cf
import json
import subprocess
import tempfile

import pandas as pd

from . import llm
from .analyses import run_battery
from .data import ROOT, SCHEMA, load
from .extra import fix_types
from .synth import SYNTHESIZERS

OUT = ROOT / "synth_results/scale.jsonl"
EPOCHS = {"ctgan": 100, "tvae": 150}
CATS = {n: ",".join(c for c, t in SCHEMA[n].items() if t == "cat" and c != "year") for n in SCHEMA}


def synthpop(name, sub, seed):
    with tempfile.TemporaryDirectory() as d:
        sub.to_csv(f"{d}/in.csv", index=False)
        subprocess.run(["Rscript", str(ROOT / "synthrep/r/synthpop_run.R"), f"{d}/in.csv", f"{d}/out", "1",
                        str(seed), CATS[name]], check=True, capture_output=True)
        return pd.read_csv(f"{d}/out_0.csv", dtype=str)


def one(job):
    name, n, draw, method = job
    import torch
    torch.set_num_threads(1)
    sub = load(name).sample(n, random_state=100 + draw).reset_index(drop=True)
    seed = 1000 * draw + 7
    if method == "real":
        syn = sub
    elif method == "synthpop":
        syn = synthpop(name, sub, seed)
    elif method == "llm":
        syn, _ = llm.synthesize(name, seed, df=sub, tag=f"_n{n}_d{draw}")
    else:
        syn = SYNTHESIZERS[method](sub, SCHEMA[name], seed, epochs=EPOCHS.get(method, 0))
    syn = fix_types(name, syn.copy())
    rows = run_battery(name, syn)
    for r in rows:
        r.update(dataset=name, n=n, draw=draw, method=method)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="2000,10000")
    ap.add_argument("--draws", type=int, default=5)
    ap.add_argument("--methods", default="real,bootstrap,marginals,synthpop,copula,tvae,ctgan")
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    done = set()
    if OUT.exists():
        done = {(r["dataset"], r["n"], r["draw"], r["method"]) for r in map(json.loads, OUT.read_text().splitlines())}
    jobs = [(nm, int(n), d, m) for m in a.methods.split(",") for nm in ["gss", "acs"]
            for n in a.sizes.split(",") for d in range(a.draws) if (nm, int(n), d, m) not in done]
    print(len(jobs), "jobs", flush=True)
    ex = cf.ThreadPoolExecutor(a.procs) if "llm" in a.methods else cf.ProcessPoolExecutor(a.procs)
    with ex, OUT.open("a") as f:
        for rows in ex.map(one, jobs):
            for r in rows:
                f.write(json.dumps(r) + "\n")
            f.flush()
            print(rows[0]["dataset"], rows[0]["n"], rows[0]["draw"], rows[0]["method"], flush=True)


if __name__ == "__main__":
    main()
