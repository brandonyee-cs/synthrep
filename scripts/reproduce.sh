#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
G=sex,race,region,marital,wrkstat,happy
A=sex,race,native,mar,puma,cow,occ

$PY scripts/get_data.py
$PY -m synthrep.data

$PY -m synthrep.run --methods bootstrap,marginals,copula --reps 10
SYN_THREADS=2 $PY -m synthrep.run --methods tvae300,ctgan300 --reps 3 --procs 2

mkdir -p data/sp
Rscript synthrep/r/synthpop_run.R data/csv/gss.csv data/sp/gss 10 7 $G
Rscript synthrep/r/synthpop_run.R data/csv/acs.csv data/sp/acs 10 7 $A
Rscript synthrep/r/synthpop_run.R data/csv/gssw.csv data/sp/gssw 5 7 $G
Rscript synthrep/r/synthpop_run.R data/csv/acsw.csv data/sp/acsw 5 7 $A
$PY -m synthrep.extra synthpop
$PY -m synthrep.extra weighted
$PY -m synthrep.design

$PY -m synthrep.published build
$PY -m synthrep.published run --methods bootstrap,marginals,synthpop,copula --reps 10
LOKY_MAX_CPU_COUNT=1 OMP_NUM_THREADS=1 $PY -m synthrep.scale --procs 2

if [ -n "${OPENROUTER_API_KEY:-}" ]; then
  for r in 0 1 2; do for n in gss acs; do $PY -m synthrep.llm --dataset $n --rep $r; done; done
  $PY -m synthrep.extra llm
  LLM_THREADS=12 $PY -m synthrep.published run --methods llm --reps 2
  $PY -m synthrep.scale --methods llm --procs 2
fi

$PY -m synthrep.analyze
$PY -m synthrep.fidelity
$PY -m synthrep.fidelity_add synthpop llm tvae300 ctgan300
$PY -m synthrep.figure
cp synth_results/figure1.pdf synth_results/figure1.png paper/
echo "Done. See synth_results/summary.md, fidelity.csv, figure1.pdf"
