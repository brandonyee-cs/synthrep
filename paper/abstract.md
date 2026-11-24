# Do Regressions on Synthetic Data Match the Original? Evidence from the GSS and the ACS

*Nyx(ius) Labs. Extended abstract, AI for Social Science Research Methods, Yale University, April 2027.*
*Markdown copy of `abstract.tex`; the .tex file is the submission version.*

**Abstract.** Statistical agencies and data archives have begun to release synthetic copies of
confidential microdata. We ask whether regressions run on such files give the answer the original data
would have given. We made synthetic copies of the General Social Survey and the American Community Survey
with four common synthesizers and re-estimated 32 published-style coefficients. Three synthesizers kept
the sign and significance of most coefficients but not their size. The fourth kept sizes on average, but
its confidence intervals were too narrow. The quality score of a popular synthesis package revealed
neither problem.

## 1. Introduction
Confidential microdata are hard to obtain. One response is to release synthetic data: a model learns the
joint distribution of the original records, and the agency publishes new records drawn from that model
(Reiter 2005). The U.S. Census Bureau has released synthetic versions of the Survey of Income and Program
Participation and the Longitudinal Business Database (Benedetto et al. 2013; Kinney et al. 2011), and
open-source packages now let any researcher make a synthetic copy of a restricted file (Nowok et al.
2016; Patki et al. 2016).

A researcher who receives a synthetic file will run the regression they would have run on the original.
For them, the useful question is narrow: will the coefficient and its confidence interval match what the
original data would have given? Following Nowok et al. (2016), we take the estimate from the original
data as the target, not the population value.

Data releasers usually describe a synthetic file with general similarity scores. These compare the
distribution of each variable and of each pair of variables in the synthetic and original files (Snoke
et al. 2018). A regression depends on more than pairs. It depends on relationships that hold after
conditioning on other variables, on interactions, and on small groups. A file can match every pair of
variables and still change a regression. We test how often this happens in practice.

Section 3 reports three results in turn:
1. Most synthesizers keep significance but shrink effects.
2. The one that keeps effect sizes gives intervals that are too narrow.
3. The similarity score warns of neither.

## 2. Data and methods
**Data.** We use two public surveys and treat each as if it were confidential.
- **GSS:** the General Social Survey cumulative file, 1972–2024 (62,472 respondents, 12 variables).
- **ACS:** the 2022 American Community Survey public-use file, restricted to Pennsylvania wage earners aged 25–64 (46,543 workers, 11 variables).

The two differ in shape. The GSS is a long series of cross-sections in which time matters. The ACS is
one large year with many-valued variables, such as 95 local areas and 23 occupation groups.

**Synthesizers.** We use four synthesizers, with package defaults except for training length:
- **Sequential CART** (Reiter 2005), the default in the R package `synthpop`.
- **A Gaussian copula**, from the Synthetic Data Vault (Patki et al. 2016).
- **CTGAN and TVAE** (Xu et al. 2019), two neural-network models, also from the Synthetic Data Vault.

We add two comparison files:
- **A bootstrap resample of the original data.** It shows how far estimates move from sampling noise alone.
- **A file in which each column is resampled on its own.** It keeps every variable's distribution but no relationships between variables, a standard baseline in this literature (Raab et al. 2017; Stadler et al. 2022).

We draw ten files per synthesizer and survey. CTGAN and TVAE train slowly on a CPU, so they get three
files each, plus one CTGAN file per survey trained for its default 300 epochs.

**Regressions.** We fit 16 OLS regressions of the kind found in published work and follow 32
coefficients:
- main effects, such as the return to schooling
- squared terms
- coefficients after fixed effects
- trends, such as the decline in women's happiness (Stevenson & Wolfers 2009)
- interactions
- gaps within small groups

Logs, squares and indicators are computed after synthesis, as a user would compute them.

**Measures.** For each coefficient and each synthetic file, we ask whether the synthetic 95% confidence
interval contains the original estimate. If the synthesizer reproduced the original distribution, this
should happen close to 95% of the time (Nowok et al. 2016); the bootstrap file checks this. We also record
whether significance at the 5% level matches the original, and the ratio of the synthetic estimate to the
original one.

## 3. Results
### 3.1 Significance survives, size does not
Table 1 gives the results for each synthesizer. The bootstrap file behaves as it should: its intervals
contain the original estimate 96% of the time. The copula, CTGAN and TVAE files keep the significance of
72–91% of coefficients, but their intervals contain the original estimate only 6–16% of the time. The
estimates are pulled toward zero: main effects shrink to between two-thirds and four-fifths of their
original size.

**Table 1.** Results by synthetic file, pooled over 32 coefficients and both surveys. The last column uses
main effects, squared terms and fixed-effects coefficients.

| Synthetic file | Same significance as original | CI contains original estimate | Synthetic / original (median) |
|---|---|---|---|
| Bootstrap of original data | 97% | 96% | 1.00 |
| CART | 93% | 67% | 1.00 |
| Gaussian copula | 72% | 6% | 0.75 |
| TVAE | 91% | 11% | 0.81 |
| CTGAN (100 / 300 epochs) | 82% / 84% | 11% / 16% | 0.68 / 0.76 |
| Independent columns | 5% | 6% | 0.00 |

The shrinkage has a simple cause. When a synthesizer fails to learn how two variables depend on each
other, it generates them as if they were closer to independent, and regression coefficients move toward
zero (Reiter 2005; Kinney et al. 2011). The extreme case is marital status in the copula files. In the
original GSS, married respondents report 0.67 more log family income than unmarried ones with the same
education, age, sex and race; in the copula files the gap is 0.00.

Because significance usually survives, a researcher who checks only whether results remain significant,
a check that Karr et al. (2006) proposed, would accept most of these files.

### 3.2 CART keeps effect sizes, but its intervals are too narrow
CART is the exception in Table 1. Its estimates are centered on the original ones, with a median ratio of
1.00. Its intervals, however, are as narrow as those from the original data, while its estimates scatter
more widely around the original values. As a result, the intervals contain the original estimate in 67%
of cases rather than 95%, and in only half of the coefficients estimated with fixed effects.

One synthetic file is a single random draw, so part of this gap could be noise. To check, we pooled the
ten CART files with the combining rule of Raab et al. (2016). If the synthesizer were correct, the pooled
estimate would differ from the original by more than synthesis noise in about 5% of coefficients. It
does so in 62%. The gap comes from the synthesis model, not from the luck of one draw.

### 3.3 The quality score does not warn the user
Figure 1 places the result from Table 1 next to the quality score that SDV reports. This score averages
how well single-variable distributions and pairwise relationships match. It gives CART 99% and every
other synthesizer 84% or more. It gives 92% to the file with independent columns, which is higher than
CTGAN and TVAE, even though no regression on that file reproduces. A score built from pairs cannot see
relationships that depend on a third variable. The propensity-score measure of Snoke et al. (2018) ranks
the files better, but it also does not say whether a particular regression will reproduce.

![Figure 1](figure1.png)

**Figure 1.** Share of synthetic confidence intervals that contain the original estimate (left) and SDV
quality score (right), by synthetic file.

## 4. Checks and limits
**Sampling noise in the original estimate.** The original estimate has its own sampling error. The
bootstrap file shows that, with no synthesis at all, intervals contain the original estimate 96% of the
time, so the shortfalls above come from synthesis.

**Training length.** Training CTGAN for its default 300 epochs instead of 100 raises coverage only from
11% to 16%.

**Choice of regressions.** We chose models typical of published work, as Karr et al. (2006) recommend. A
check can favor a synthesizer whose model resembles the analysis (Snoke et al. 2018); our regressions
condition on variables in ways tree splits capture well, which may help CART.

**Two surveys.** The GSS and ACS differ in shape, and the pattern holds in both. CART's intervals contain
the original estimate 79% of the time in the GSS and 54% in the ACS, and the other synthesizers stay
below 20% in each. Two surveys cannot settle the question, and we plan to add more.

**Implementation and privacy.** Our CART synthesizer is a Python version of the `synthpop` method that
codes categories as ordered numbers; we will rerun it with `synthpop` itself. None of the files adds
formal privacy protection, which generally lowers accuracy (Stadler et al. 2022), so our results describe
the best these synthesizers can do.

## 5. Conclusion
For the regressions social scientists publish, a synthetic file can keep significance while changing
effect sizes, or keep effect sizes while giving intervals that are too narrow. The similarity score that
comes with the file does not show either problem. We suggest that releasers state a set of standard
regressions for each file and report how often their intervals contain the original estimates, so that
users can see what the file supports. Before the workshop we will add synthesizers with formal privacy
protection, more surveys, published replication files, and survey weights. Code and results:
https://github.com/brandonyee-cs/synthrep.

*Requested format: lightning talk or talk; poster acceptable.*

## References
- Benedetto, G., Stinson, M., & Abowd, J. M. (2013). The creation and use of the SIPP Synthetic Beta. U.S. Census Bureau working paper.
- Karr, A. F., Kohnen, C. N., Oganian, A., Reiter, J. P., & Sanil, A. P. (2006). A framework for evaluating the utility of data altered to protect confidentiality. *The American Statistician*, 60(3), 224–232.
- Kinney, S. K., Reiter, J. P., Reznek, A. P., Miranda, J., Jarmin, R. S., & Abowd, J. M. (2011). Towards unrestricted public use business microdata: The synthetic Longitudinal Business Database. *International Statistical Review*, 79(3), 362–384.
- Nowok, B., Raab, G. M., & Dibben, C. (2016). synthpop: Bespoke creation of synthetic data in R. *Journal of Statistical Software*, 74(11), 1–26.
- Patki, N., Wedge, R., & Veeramachaneni, K. (2016). The Synthetic Data Vault. *IEEE DSAA*, 399–410.
- Raab, G. M., Nowok, B., & Dibben, C. (2016). Practical data synthesis for large samples. *Journal of Privacy and Confidentiality*, 7(3), 67–97.
- Raab, G. M., Nowok, B., & Dibben, C. (2017). Guidelines for producing useful synthetic data. arXiv:1712.04078.
- Reiter, J. P. (2005). Using CART to generate partially synthetic public use microdata. *Journal of Official Statistics*, 21(3), 441–462.
- Snoke, J., Raab, G. M., Nowok, B., Dibben, C., & Slavković, A. (2018). General and specific utility measures for synthetic data. *JRSS Series A*, 181(3), 663–688.
- Stadler, T., Oprisanu, B., & Troncoso, C. (2022). Synthetic data – anonymisation groundhog day. *USENIX Security Symposium*.
- Stevenson, B., & Wolfers, J. (2009). The paradox of declining female happiness. *American Economic Journal: Economic Policy*, 1(2), 190–225.
- Xu, L., Skoularidou, M., Cuesta-Infante, A., & Veeramachaneni, K. (2019). Modeling tabular data using conditional GAN. *NeurIPS*, 32.
