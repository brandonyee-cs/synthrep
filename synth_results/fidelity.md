## Generic fidelity vs analysis-specific validity (replicate 0)

`sdv_quality`: SDV Quality Report score (higher = 'better'). `pmse_ratio`: 1 = indistinguishable from real.

| dataset / synthesizer | sdv_quality | pmse_ratio | ci_overlap | covers | sig_ok |
|---|---|---|---|---|---|
| gss / bootstrap | 99% | 0.7 | 0.80 | 95% | 99% |
| gss / cart | 99% | 5.4 | 0.66 | 79% | 98% |
| gss / copula | 91% | 54.2 | 0.02 | 0% | 71% |
| gss / tvae | 82% | 199.4 | 0.07 | 6% | 88% |
| gss / ctgan | 88% | 55.4 | 0.09 | 8% | 88% |
| gss / ctgan300 | 89% | 53.2 | 0.19 | 18% | 88% |
| gss / marginals | 91% | 56.5 | 0.02 | 1% | 3% |
| acs / bootstrap | 99% | 0.7 | 0.80 | 97% | 95% |
| acs / cart | 99% | 1.5 | 0.52 | 54% | 87% |
| acs / copula | 90% | 114.4 | 0.14 | 13% | 73% |
| acs / tvae | 87% | 83.9 | 0.16 | 18% | 93% |
| acs / ctgan | 84% | 56.5 | 0.14 | 16% | 76% |
| acs / ctgan300 | 87% | 57.7 | 0.09 | 13% | 80% |
| acs / marginals | 92% | 87.9 | 0.11 | 12% | 7% |

Spearman rank correlation with mean CI overlap: SDV quality 0.52, pMSE ratio -0.66 (n=14 synthesizer-dataset files).
