"""Figure 1: coverage of the original estimate and SDV quality score, by synthetic file.

  python -m synthrep.figure
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .data import ROOT

D = ROOT / "synth_results"
LABEL = {"bootstrap": "Resampled original data", "cart": "CART",
         "copula": "Gaussian copula", "tvae": "TVAE", "ctgan": "CTGAN",
         "ctgan300": "CTGAN, 300 epochs", "marginals": "Independent columns\n(no relationships)"}
ORDER = ["bootstrap", "cart", "copula", "tvae", "ctgan", "ctgan300", "marginals"]
INK, MUTED, GRID, SERIES, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6", "#fcfcfb"


def main():
    m = pd.read_csv(D / "metrics.csv")
    f = pd.read_csv(D / "fidelity.csv")
    cov = m.groupby("method").covers.mean()
    q = f.groupby("method").sdv_quality.mean()
    rows = [r for r in ORDER if r in cov.index and r in q.index]
    y = range(len(rows))[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True, facecolor=SURF)
    for ax, vals, title, ref in [
        (axes[0], cov, "Synthetic 95% CI contains\nthe original estimate", 0.95),
        (axes[1], q, "SDV quality score", None)]:
        ax.set_facecolor(SURF)
        v = [vals[r] for r in rows]
        ax.hlines(list(y), 0, v, color=GRID, lw=2, zorder=1)
        ax.scatter(v, list(y), s=70, color=SERIES, zorder=3, edgecolor=SURF, linewidth=2)
        for yi, vi in zip(y, v):
            ax.text(vi + 0.03, yi, f"{100 * vi:.0f}%", va="center", fontsize=9, color=INK)
        if ref:
            ax.axvline(ref, color=MUTED, lw=1, ls=(0, (3, 3)), zorder=0)
            ax.text(ref - 0.02, len(rows) - 1.5, "nominal\n95%", ha="right", va="center", fontsize=8, color=MUTED)
        ax.set_xlim(0, 1.12)
        ax.set_xticks([0, .25, .5, .75, 1])
        ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8, color=MUTED)
        ax.set_title(title, fontsize=10, color=INK, loc="left")
        for s in ["top", "right", "left"]:
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", color=GRID)
    axes[0].set_yticks(list(y))
    axes[0].set_yticklabels([LABEL[r] for r in rows], fontsize=9, color=INK)
    fig.text(0.01, 0.01, "32 coefficients from 16 regressions on the GSS (1972-2024) and ACS (2022, Pennsylvania). "
             "Quality score from the first synthetic file of each kind.", fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(D / "figure1.png", dpi=200, facecolor=SURF)
    print("wrote", D / "figure1.png")


if __name__ == "__main__":
    main()
