import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .data import ROOT

D = ROOT / "synth_results"
LABEL = {"bootstrap": "Bootstrap of original data", "synthpop": "CART (synthpop)", "copula": "Gaussian copula",
         "tvae300": "TVAE", "ctgan300": "CTGAN", "llm": "LLM", "marginals": "Independent columns"}
ORDER = ["bootstrap", "synthpop", "copula", "tvae300", "ctgan300", "llm", "marginals"]
INK, MUTED, GRID, COV, QUAL = "#1a1a1a", "#6b6b6b", "#e6e6e6", "#1f5fae", "#9a9a9a"

plt.rcParams.update({"font.family": "serif", "font.serif": ["CMU Serif", "Latin Modern Roman", "Computer Modern Roman",
                                                            "DejaVu Serif"],
                     "mathtext.fontset": "cm", "font.size": 9, "axes.unicode_minus": False, "pdf.fonttype": 42})


def main():
    m = pd.read_csv(D / "metrics.csv")
    f = pd.read_csv(D / "fidelity.csv")
    cov = m.groupby("method").covers.mean() * 100
    q = f.groupby("method").sdv_quality.mean() * 100
    rows = [r for r in ORDER if r in cov.index and r in q.index]
    y = list(range(len(rows)))[::-1]
    fig, ax = plt.subplots(figsize=(6.0, 2.25))
    ax.axvline(95, color=MUTED, lw=0.8, ls=(0, (2, 2)), zorder=0)
    ax.text(95, len(rows) - 0.35, "95%", ha="center", va="bottom", fontsize=8, color=MUTED)
    for yi, r in zip(y, rows):
        c, s = cov[r], q[r]
        ax.plot([c, s], [yi, yi], color=GRID, lw=2.2, zorder=1, solid_capstyle="round")
        ax.scatter(s, yi, s=34, facecolor="white", edgecolor=QUAL, linewidth=1.3, zorder=3)
        ax.scatter(c, yi, s=34, color=COV, zorder=4)
        ax.text(c - 2.2, yi, f"{c:.0f}", ha="right", va="center", fontsize=8, color=COV)
    ax.set_yticks(y)
    ax.set_yticklabels([LABEL[r] for r in rows], color=INK)
    ax.set_xlim(-8, 103)
    ax.set_ylim(-0.6, len(rows) - 0.1)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], color=MUTED, fontsize=8)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#bdbdbd")
    ax.tick_params(axis="y", length=0, pad=4)
    ax.tick_params(axis="x", color="#bdbdbd", length=3)
    ax.scatter([], [], s=34, color=COV, label="Coverage of the original estimate")
    ax.scatter([], [], s=34, facecolor="white", edgecolor=QUAL, linewidth=1.3, label="Quality score")
    ax.legend(loc="lower center", bbox_to_anchor=(0.42, 1.04), ncol=2, frameon=False, fontsize=8.5,
              handletextpad=0.3, columnspacing=1.6)
    fig.tight_layout(pad=0.3)
    for ext in ["pdf", "png"]:
        fig.savefig(D / f"figure1.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.02)
    print("wrote", D / "figure1.pdf")


if __name__ == "__main__":
    main()
