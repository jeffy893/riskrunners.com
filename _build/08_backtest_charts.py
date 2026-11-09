#!/usr/bin/env python3
"""
Back-test step 3 — charts for the experiment page, base64-embedded.
  (a) intra-portfolio correlation heatmap (estimation window) — proves the
      names co-move, the precondition for a pure play.
  (b) cumulative short-P&L path through the event window: the weighted basket
      short vs shorting SPY, on $100.
All values come from _build/backtest_results.json (real data). No simulation.
"""
import os, json, io, base64
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = json.load(open(os.path.join(HERE, "backtest_results.json")))
OUT = os.path.join(HERE, "backtest_charts.json")

CREAM = "#faf6ef"; INK = "#2b2621"; GOLD = "#c8912f"; RUST = "#a1542f"
SLATE = "#4a5b6b"; TEAL = "#19a6c8"; GREEN = "#3fb27f"
plt.rcParams.update({
    "figure.facecolor": CREAM, "axes.facecolor": CREAM, "savefig.facecolor": CREAM,
    "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.edgecolor": "#d8ccb8", "font.size": 11, "font.family": "sans-serif",
})


def uri(fig):
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=115, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def corr_chart(r):
    C = np.array(r["corr"]); t = r["tickers"]; k = len(t)
    fig, ax = plt.subplots(figsize=(6.6, 5.8))
    im = ax.imshow(C, cmap="YlGnBu", vmin=0, vmax=1)
    ax.set_xticks(range(k)); ax.set_yticks(range(k))
    ax.set_xticklabels(t, fontsize=8, rotation=45, ha="right")
    ax.set_yticklabels(t, fontsize=8)
    for i in range(k):
        for j in range(k):
            ax.text(j, i, f"{C[i,j]:.2f}", ha="center", va="center",
                    fontsize=7, color="white" if C[i, j] > 0.6 else "#333")
    ax.set_title(f"Do they move together? Daily-return correlation\n"
                 f"(estimation window {r['est_window'][0]} to {r['est_window'][1]})",
                 fontsize=10.5)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); cb.ax.tick_params(labelsize=7)
    return uri(fig)


def pnl_chart(r):
    d = r["path"]["dates"]; b = r["path"]["basket"]; s = r["path"]["spy"]
    x = range(len(d))
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.axhline(0, color="#999", lw=1)
    ax.plot(x, b, color=GREEN, lw=2.4, marker="o", ms=4,
            label=f"Short the pure-play basket  (end \\${b[-1]:+.2f})")
    ax.plot(x, s, color=SLATE, lw=2, ls="--", marker="s", ms=3,
            label=f"Short the market (SPY)  (end \\${s[-1]:+.2f})")
    ax.fill_between(x, 0, b, where=[v >= 0 for v in b], color=GREEN, alpha=0.10)
    ax.set_xticks(list(x))
    ax.set_xticklabels([dd[5:] for dd in d], fontsize=8, rotation=45, ha="right")
    ax.set_ylabel(r"Gain on a \$100 short (\$)")
    ax.set_title(f"Out-of-sample hedge P&L through the event\n{r['event']['label']} "
                 f"({r['evt_window'][0]} to {r['evt_window'][1]})", fontsize=10.5)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.grid(axis="y", color="#e4dac8", lw=0.8); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    return uri(fig)


def main():
    charts = {}
    for key, r in RES.items():
        charts[key] = {"corr": corr_chart(r), "pnl": pnl_chart(r)}
        print(f"  {key}: corr + pnl charts")
    json.dump(charts, open(OUT, "w"))
    print("saved", OUT)


if __name__ == "__main__":
    main()
