import argparse
import json
import os
import pathlib
import time
from multiprocessing import Pool

from .analyses import run_battery
from .data import ROOT, load
from .synth import synthesize

EPOCHS = {"ctgan300": 300, "tvae300": 300}


def one(job):
    name, method, rep, epochs, save_dir = job
    import torch
    torch.set_num_threads(int(os.environ.get("SYN_THREADS", 1)))
    df = load(name)
    seed = 1000 * rep + 7
    t0 = time.time()
    syn = synthesize(method, name, df, seed, epochs=epochs)
    secs = time.time() - t0
    if rep == 0 and save_dir:
        syn.to_pickle(pathlib.Path(save_dir) / f"{name}_{method}_rep0.pkl")
    rows = run_battery(name, syn)
    for r in rows:
        r.update(dataset=name, method=method, rep=rep, synth_secs=round(secs, 1))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="gss,acs")
    ap.add_argument("--methods", default="bootstrap,marginals,copula")
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--out", default=str(ROOT / "synth_results/estimates.jsonl"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    save_dir = out.parent / "samples"
    save_dir.mkdir(exist_ok=True)

    real_path = out.parent / "real.jsonl"
    if not real_path.exists():
        with real_path.open("w") as f:
            for name in ["gss", "acs"]:
                for r in run_battery(name, load(name)):
                    r.update(dataset=name, method="real", rep=0)
                    f.write(json.dumps(r) + "\n")

    done = set()
    if out.exists():
        done = {(r["dataset"], r["method"], r["rep"]) for r in map(json.loads, out.read_text().splitlines())}
    jobs = [(n, m, k, EPOCHS.get(m, 0), str(save_dir))
            for m in a.methods.split(",") for n in a.datasets.split(",") for k in range(a.reps)
            if (n, m, k) not in done]
    print(f"{len(jobs)} synthetic datasets to generate", flush=True)
    with Pool(a.procs, maxtasksperchild=1) as pool, out.open("a") as f:
        for i, rows in enumerate(pool.imap_unordered(one, jobs), 1):
            for r in rows:
                f.write(json.dumps(r) + "\n")
            f.flush()
            print(f"  {i}/{len(jobs)} {rows[0]['dataset']} {rows[0]['method']} rep{rows[0]['rep']} "
                  f"({rows[0]['synth_secs']}s)", flush=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
