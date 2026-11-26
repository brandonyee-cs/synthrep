# Can synthetic data replace the real thing? Pilot results

Real data: GSS 1972-2024 (n=62,472), ACS 2022 Pennsylvania workers (n=46,543). 32 published-style coefficients from 16 models.
Replicates per synthesizer: bootstrap 10, synthpop 10, cart 10, copula 10, tvae 3, tvae300 3, ctgan 3, ctgan300 3, llm 3, marginals 10. `bootstrap` = resampled real data (sampling-noise reference); `marginals` = no joint structure (floor).

## 1. Headline: share of coefficients whose significance verdict matches the real data

| synthesizer | main | nonlinear | fe_adjusted | trend | interaction | subgroup |
|---|---|---|---|---|---|---|
| bootstrap | 100% | 100% | 100% | 93% | 80% | 95% |
| synthpop | 93% | 100% | 100% | 73% | 70% | 98% |
| cart | 93% | 100% | 100% | 87% | 70% | 100% |
| copula | 73% | 0% | 100% | 67% | 33% | 100% |
| tvae | 96% | 100% | 100% | 89% | 44% | 92% |
| tvae300 | 98% | 83% | 100% | 78% | 67% | 100% |
| ctgan | 78% | 67% | 100% | 89% | 56% | 100% |
| ctgan300 | 91% | 100% | 100% | 56% | 67% | 92% |
| llm | 93% | 100% | 100% | 11% | 44% | 100% |
| marginals | 8% | 0% | 2% | 7% | 0% | 2% |

## 2. Mean CI overlap with the real-data CI (1 = identical, 0 = disjoint)

| synthesizer | main | nonlinear | fe_adjusted | trend | interaction | subgroup |
|---|---|---|---|---|---|---|
| bootstrap | 0.80 | 0.81 | 0.81 | 0.81 | 0.79 | 0.77 |
| synthpop | 0.39 | 0.44 | 0.24 | 0.63 | 0.65 | 0.51 |
| cart | 0.59 | 0.57 | 0.46 | 0.70 | 0.73 | 0.61 |
| copula | 0.03 | 0.00 | 0.00 | 0.01 | 0.24 | 0.28 |
| tvae | 0.11 | 0.03 | 0.00 | 0.10 | 0.27 | 0.17 |
| tvae300 | 0.11 | 0.10 | 0.19 | 0.12 | 0.28 | 0.10 |
| ctgan | 0.06 | 0.00 | 0.05 | 0.36 | 0.18 | 0.23 |
| ctgan300 | 0.08 | 0.33 | 0.02 | 0.11 | 0.39 | 0.39 |
| llm | 0.07 | 0.00 | 0.00 | 0.14 | 0.25 | 0.17 |
| marginals | 0.05 | 0.00 | 0.00 | 0.09 | 0.18 | 0.08 |

## 3. Share of synthetic 95% CIs that contain the real estimate

| synthesizer | main | nonlinear | fe_adjusted | trend | interaction | subgroup |
|---|---|---|---|---|---|---|
| bootstrap | 95% | 95% | 96% | 93% | 100% | 100% |
| synthpop | 41% | 50% | 16% | 80% | 70% | 60% |
| cart | 67% | 60% | 50% | 77% | 87% | 70% |
| copula | 0% | 0% | 0% | 0% | 33% | 25% |
| tvae | 13% | 0% | 0% | 0% | 33% | 17% |
| tvae300 | 11% | 17% | 13% | 11% | 44% | 8% |
| ctgan | 7% | 0% | 7% | 33% | 22% | 17% |
| ctgan300 | 9% | 33% | 0% | 11% | 44% | 42% |
| llm | 4% | 0% | 0% | 11% | 33% | 0% |
| marginals | 7% | 0% | 0% | 3% | 17% | 8% |

## 4. Median |standardized bias| (in real-data SEs)

| synthesizer | main | nonlinear | fe_adjusted | trend | interaction | subgroup |
|---|---|---|---|---|---|---|
| bootstrap | 0.7 | 0.5 | 0.6 | 0.5 | 0.8 | 0.9 |
| synthpop | 2.5 | 2.4 | 3.4 | 1.6 | 1.5 | 1.8 |
| cart | 1.5 | 1.6 | 2.1 | 1.1 | 1.1 | 1.4 |
| copula | 8.1 | 26.1 | 7.6 | 4.9 | 6.7 | 5.6 |
| tvae | 17.2 | 13.8 | 23.3 | 5.5 | 5.3 | 5.9 |
| tvae300 | 16.5 | 17.7 | 17.0 | 7.9 | 3.5 | 5.8 |
| ctgan | 13.3 | 15.9 | 15.2 | 3.1 | 6.0 | 3.7 |
| ctgan300 | 8.5 | 3.2 | 10.9 | 5.0 | 3.1 | 2.8 |
| llm | 21.1 | 15.8 | 22.7 | 28.2 | 9.2 | 7.1 |
| marginals | 31.0 | 23.3 | 31.0 | 5.6 | 9.6 | 10.6 |

## 5. Overall by synthesizer and dataset

| synthesizer | dataset | sig. verdict match | CI overlap | real est. covered | sign match | median SE ratio | analyses failed | rows dropped (invalid values) |
|---|---|---|---|---|---|---|---|---|
| bootstrap | gss | 99% | 0.80 | 95% | 100% | 1.00 | 0% | 0% |
| bootstrap | acs | 95% | 0.80 | 97% | 97% | 1.00 | 0% | 0% |
| synthpop | gss | 95% | 0.55 | 63% | 100% | 1.00 | 0% | 0% |
| synthpop | acs | 87% | 0.29 | 28% | 97% | 1.01 | 0% | 0% |
| cart | gss | 98% | 0.66 | 79% | 100% | 1.00 | 0% | 0% |
| cart | acs | 87% | 0.52 | 54% | 99% | 1.01 | 0% | 0% |
| copula | gss | 71% | 0.02 | 0% | 82% | 1.06 | 0% | 0% |
| copula | acs | 73% | 0.14 | 13% | 93% | 1.20 | 0% | 0% |
| tvae | gss | 88% | 0.07 | 6% | 90% | 0.59 | 0% | 0% |
| tvae | acs | 93% | 0.16 | 18% | 93% | 0.94 | 0% | 0% |
| tvae300 | gss | 88% | 0.04 | 2% | 92% | 0.55 | 0% | 0% |
| tvae300 | acs | 98% | 0.25 | 29% | 98% | 0.97 | 0% | 0% |
| ctgan | gss | 88% | 0.09 | 8% | 92% | 0.97 | 0% | 0% |
| ctgan | acs | 76% | 0.14 | 16% | 87% | 1.02 | 0% | 0% |
| ctgan300 | gss | 90% | 0.16 | 14% | 96% | 0.99 | 0% | 0% |
| ctgan300 | acs | 84% | 0.16 | 20% | 93% | 1.07 | 0% | 0% |
| llm | gss | 78% | 0.03 | 2% | 84% | 0.78 | 0% | 0% |
| llm | acs | 89% | 0.16 | 11% | 98% | 0.56 | 0% | 0% |
| marginals | gss | 3% | 0.02 | 1% | 44% | 1.04 | 0% | 0% |
| marginals | acs | 7% | 0.11 | 12% | 48% | 1.09 | 0% | 0% |

## 6. Pooling all synthetic copies (synthpop combining rule): share of coefficients where the
pooled estimate differs from the real one beyond synthesis noise (|z| > 1.96; 5% expected if valid)

| synthesizer | main | nonlinear | fe_adjusted | trend | interaction | subgroup |
|---|---|---|---|---|---|---|
| bootstrap | 0% | 0% | 0% | 0% | 0% | 0% |
| synthpop | 80% | 50% | 100% | 100% | 67% | 75% |
| cart | 60% | 50% | 80% | 67% | 33% | 75% |
| copula | 100% | 100% | 100% | 100% | 100% | 100% |
| tvae | 93% | 100% | 100% | 67% | 100% | 100% |
| tvae300 | 93% | 100% | 100% | 100% | 67% | 100% |
| ctgan | 100% | 100% | 80% | 100% | 100% | 100% |
| ctgan300 | 100% | 100% | 80% | 100% | 67% | 75% |
| llm | 93% | 100% | 100% | 100% | 67% | 100% |
| marginals | 93% | 100% | 100% | 100% | 100% | 100% |


## 7. Coefficient-level detail (mean CI overlap; real estimate and SE shown)

| coefficient | type | real est (se) | bootstrap | synthpop | cart | copula | tvae | tvae300 | ctgan | ctgan300 | llm | marginals |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| acs/A1 black (Mincer wage equation) | main | -0.173 (0.019) | 0.80 | 0.06 | 0.16 | 0.00 | 0.42 | 0.28 | 0.00 | 0.21 | 0.47 | 0.00 |
| acs/A1 exp2 (Mincer wage equation) | nonlinear | -0.040 (0.003) | 0.79 | 0.07 | 0.38 | 0.00 | 0.06 | 0.19 | 0.00 | 0.52 | 0.00 | 0.00 |
| acs/A1 female (Mincer wage equation) | main | -0.257 (0.007) | 0.78 | 0.18 | 0.62 | 0.00 | 0.00 | 0.00 | 0.07 | 0.26 | 0.00 | 0.00 |
| acs/A1 lnhrs (Mincer wage equation) | main | 1.229 (0.018) | 0.82 | 0.44 | 0.62 | 0.00 | 0.00 | 0.00 | 0.26 | 0.00 | 0.50 | 0.00 |
| acs/A1 schl (Mincer wage equation) | main | 0.113 (0.002) | 0.84 | 0.12 | 0.68 | 0.00 | 0.26 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| acs/A2 female (Gender gap with occupation FE) | fe_adjusted | -0.240 (0.008) | 0.80 | 0.23 | 0.46 | 0.00 | 0.00 | 0.44 | 0.00 | 0.00 | 0.00 | 0.00 |
| acs/A2 schl (Gender gap with occupation FE) | fe_adjusted | 0.081 (0.002) | 0.76 | 0.13 | 0.11 | 0.00 | 0.00 | 0.13 | 0.00 | 0.00 | 0.00 | 0.00 |
| acs/A3 female (Gender gap with occupation and PUMA FE) | fe_adjusted | -0.236 (0.008) | 0.81 | 0.27 | 0.43 | 0.00 | 0.00 | 0.38 | 0.00 | 0.00 | 0.00 | 0.00 |
| acs/A4 ba (Return to BA by race) | main | 0.609 (0.008) | 0.77 | 0.39 | 0.65 | 0.00 | 0.00 | 0.30 | 0.39 | 0.00 | 0.00 | 0.00 |
| acs/A4 ba:black (Return to BA by race) | interaction | -0.083 (0.041) | 0.83 | 0.60 | 0.61 | 0.73 | 0.22 | 0.39 | 0.55 | 0.50 | 0.76 | 0.54 |
| acs/A5 married (Marriage premium by sex) | main | 0.292 (0.010) | 0.80 | 0.00 | 0.42 | 0.00 | 0.00 | 0.00 | 0.00 | 0.21 | 0.00 | 0.00 |
| acs/A5 married:female (Marriage premium by sex) | interaction | -0.174 (0.014) | 0.76 | 0.45 | 0.85 | 0.00 | 0.60 | 0.44 | 0.00 | 0.01 | 0.00 | 0.00 |
| acs/A6 female (Gender gap among Asian workers) | subgroup | -0.248 (0.042) | 0.85 | 0.61 | 0.82 | 0.35 | 0.14 | 0.14 | 0.21 | 0.39 | 0.00 | 0.02 |
| acs/A7 female (Gender gap among Black workers) | subgroup | -0.119 (0.037) | 0.71 | 0.74 | 0.71 | 0.75 | 0.14 | 0.28 | 0.63 | 0.27 | 0.67 | 0.29 |
| acs/A8 foreign (Immigrant wage gap) | main | 0.004 (0.016) | 0.81 | 0.02 | 0.26 | 0.23 | 0.59 | 0.80 | 0.00 | 0.04 | 0.05 | 0.81 |
| gss/G1 age2 (Family-income function) | nonlinear | -0.042 (0.001) | 0.82 | 0.81 | 0.75 | 0.00 | 0.00 | 0.00 | 0.00 | 0.15 | 0.00 | 0.00 |
| gss/G1 black (Family-income function) | main | -0.351 (0.012) | 0.75 | 0.02 | 0.19 | 0.00 | 0.17 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| gss/G1 educ (Family-income function) | main | 0.111 (0.001) | 0.77 | 0.46 | 0.68 | 0.26 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| gss/G1 female (Family-income function) | main | -0.163 (0.007) | 0.90 | 0.78 | 0.73 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| gss/G1 married (Family-income function) | main | 0.672 (0.007) | 0.77 | 0.82 | 0.72 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| gss/G2 educ:female (Gender x education in income) | interaction | 0.023 (0.002) | 0.76 | 0.89 | 0.72 | 0.00 | 0.00 | 0.00 | 0.00 | 0.66 | 0.00 | 0.00 |
| gss/G3 attend (Correlates of happiness) | main | 0.019 (0.001) | 0.74 | 0.38 | 0.80 | 0.00 | 0.00 | 0.00 | 0.00 | 0.12 | 0.00 | 0.00 |
| gss/G3 childs (Correlates of happiness) | main | -0.005 (0.001) | 0.85 | 0.75 | 0.83 | 0.00 | 0.24 | 0.14 | 0.17 | 0.24 | 0.00 | 0.01 |
| gss/G3 lninc (Correlates of happiness) | main | 0.027 (0.002) | 0.72 | 0.63 | 0.70 | 0.00 | 0.00 | 0.11 | 0.00 | 0.16 | 0.00 | 0.00 |
| gss/G3 married (Correlates of happiness) | main | 0.153 (0.004) | 0.80 | 0.75 | 0.83 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| gss/G4 female:yr10 (Declining female happiness (Stevenson & Wolfers 2009)) | trend | -0.007 (0.002) | 0.78 | 0.53 | 0.76 | 0.02 | 0.09 | 0.07 | 0.59 | 0.33 | 0.43 | 0.26 |
| gss/G4 yr10 (Declining female happiness (Stevenson & Wolfers 2009)) | trend | -0.009 (0.002) | 0.82 | 0.62 | 0.75 | 0.00 | 0.21 | 0.00 | 0.47 | 0.00 | 0.00 | 0.00 |
| gss/G5 black (Black-white income gap, 2010+) | subgroup | -0.556 (0.023) | 0.77 | 0.23 | 0.33 | 0.00 | 0.27 | 0.00 | 0.00 | 0.62 | 0.00 | 0.00 |
| gss/G6 black (Black-white income gap, 1970s) | subgroup | -0.419 (0.028) | 0.77 | 0.45 | 0.57 | 0.00 | 0.14 | 0.00 | 0.08 | 0.27 | 0.00 | 0.00 |
| gss/G7 cohort10 (Religious attendance by birth cohort) | trend | -0.291 (0.007) | 0.83 | 0.74 | 0.58 | 0.00 | 0.00 | 0.28 | 0.00 | 0.00 | 0.00 | 0.00 |
| gss/G8 educ (Income function with region and year FE) | fe_adjusted | 0.126 (0.001) | 0.82 | 0.06 | 0.59 | 0.00 | 0.00 | 0.00 | 0.25 | 0.00 | 0.00 | 0.00 |
| gss/G8 female (Income function with region and year FE) | fe_adjusted | -0.222 (0.007) | 0.86 | 0.51 | 0.71 | 0.00 | 0.00 | 0.00 | 0.00 | 0.12 | 0.00 | 0.00 |
