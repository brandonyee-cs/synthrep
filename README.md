# synthrep: Do regressions on synthetic data match the original?

Statistical agencies and data archives have begun to release synthetic copies of confidential
microdata. This repository reruns 32 published-style regression coefficients on synthetic copies of the
GSS and the ACS and checks whether they match the estimates from the original data, and whether the
quality score that comes with the synthetic file shows the difference.

Pilot for the Yale workshop *AI for Social Science Research Methods* (April 2027). Extended abstract:
[`paper/abstract.tex`](paper/abstract.tex) (Markdown version: [`paper/abstract.md`](paper/abstract.md)).

![Figure 1](synth_results/figure1.png)

## Results
| synthetic file | CI contains original estimate | same significance as original | synthetic / original (median) | SDV quality score |
|---|---|---|---|---|
| bootstrap of original data | 96% | 97% | 1.00 | 99% |
| CART | 67% | 93% | 1.00 | 99% |
| Gaussian copula | 6% | 72% | 0.75 | 91% |
| TVAE | 11% | 91% | 0.81 | 84% |
| CTGAN (100 / 300 epochs) | 11% / 16% | 82% / 84% | 0.68 / 0.76 | 86% / 88% |
| independent columns | 6% | 5% | 0.00 | 92% |

1. The copula, CTGAN and TVAE files keep the significance of most coefficients, but their intervals rarely contain the original estimate.
2. CART keeps effect sizes, but its intervals are too narrow: they contain the original estimate 67% of the time instead of 95%.
3. The SDV quality score shows neither problem. It scores a file with no relationships between variables at 92%.

Full tables: [`synth_results/summary.md`](synth_results/summary.md) and [`synth_results/fidelity.md`](synth_results/fidelity.md).

## Design
- **Data** (public, no registration):
  - GSS cumulative file 1972–2024 (NORC; n = 62,472)
  - 2022 ACS 1-year PUMS, Pennsylvania wage earners aged 25–64 (U.S. Census Bureau; n = 46,543)
- **Synthesizers:**
  - sequential CART
  - Gaussian copula, CTGAN and TVAE (via [SDV](https://github.com/sdv-dev/SDV))
  - comparison files: a bootstrap of the original data, and a file with each column resampled on its own
- **Regressions:** 16 OLS models of the kind found in published work; 32 coefficients, grouped as main effects, squared terms, fixed-effects coefficients, trends, interactions and subgroup gaps. Derived variables are computed after synthesis.
- **Measures:**
  - whether the synthetic 95% CI contains the original estimate
  - whether significance matches
  - the ratio of the synthetic to the original estimate
  - also: CI overlap (Karr et al. 2006), pooled-copies test (Raab, Nowok & Dibben 2016), SDV quality score, pMSE (Snoke et al. 2018)

## Reproduce
Requires Python 3.12 and about 3 hours on 4 CPU cores. No GPU or API keys.
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # CPU torch: add --extra-index-url https://download.pytorch.org/whl/cpu
bash scripts/reproduce.sh         # downloads data, synthesizes, analyzes, draws the figure
```
Or step by step:
```bash
python scripts/get_data.py                                         # GSS + ACS downloads (no login)
python -m synthrep.data                                            # analytic tables
python -m synthrep.run --methods bootstrap,marginals,cart,copula --reps 10
python -m synthrep.run --methods tvae,ctgan --reps 3 --procs 4     # ~1.5 h
SYN_THREADS=2 python -m synthrep.run --methods ctgan300 --reps 1 --procs 2
python -m synthrep.analyze && python -m synthrep.fidelity && python -m synthrep.figure
```
`synth_results/` ships with the pilot's outputs:
- `estimates.jsonl`: every coefficient on every synthetic file
- `real.jsonl`: estimates from the original data
- `metrics.csv`, `combined.csv`, `fidelity.csv`: computed metrics

`run.py` is resumable. Delete `synth_results/estimates.jsonl` to regenerate from scratch.

The pilot used GSS release R3a (`gss7224_r3a.dta`). If NORC has since updated the file, results can differ slightly.

## Layout
| Path | What |
|---|---|
| `synthrep/data.py` | builds the GSS and ACS analytic tables |
| `synthrep/synth.py` | synthesizers (to add one, register a function in `SYNTHESIZERS`) |
| `synthrep/analyses.py` | the 16 published-style models, with coefficients tagged by type |
| `synthrep/run.py` | generates synthetic copies and runs the analysis battery |
| `synthrep/analyze.py` | replication metrics → `synth_results/summary.md` |
| `synthrep/fidelity.py` | quality scores vs replication → `synth_results/fidelity.md` |
| `synthrep/figure.py` | `synth_results/figure1.png` |
| `scripts/` | data download and full reproduction |
| `paper/` | extended abstract (.tex and .md) |

## Limitations
1. **Training budget:** CTGAN and TVAE have 3 replicates each in the main run (100 and 150 epochs). A 300-epoch CTGAN check is included.
2. **Approximate CART:** the CART synthesizer is a Python implementation of sequential CART with ordinal-coded categorical predictors, not R `synthpop` itself.
3. **Unweighted analyses.** The original-data estimate is the target; its own sampling error is measured by the bootstrap file.

## Data
Raw data are not redistributed here; `scripts/get_data.py` fetches them from the original sources.
- GSS: Davern, M., Bautista, R., Freese, J., Herd, P., & Morgan, S. L. General Social Survey 1972–2024. NORC at the University of Chicago. gss.norc.org.
- ACS: U.S. Census Bureau, American Community Survey 2022 1-year Public Use Microdata Sample.

## License
Code: MIT (see `LICENSE`).
