#!/usr/bin/env bash
# Full reproduction of the pilot (~2-3 hours on 4 CPU cores).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
$PY scripts/get_data.py
$PY -m synthrep.data
$PY -m synthrep.run --methods bootstrap,marginals,cart,copula --reps 10
$PY -m synthrep.run --methods tvae,ctgan --reps 3 --procs 4
SYN_THREADS=2 $PY -m synthrep.run --methods ctgan300 --reps 1 --procs 2
$PY -m synthrep.analyze
$PY -m synthrep.fidelity
$PY -m synthrep.figure
echo "Done. See synth_results/summary.md, fidelity.md, figure1.png"
