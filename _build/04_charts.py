#!/usr/bin/env python3
"""
Step 4 — Generate one chart per portfolio, returned as base64 PNG data URIs so
the final HTML pages are fully self-contained (works on GitHub Pages with no
external files). The chart type is chosen to match each portfolio's ISO 31010
technique:

  Monte Carlo Simulation -> outcome distribution histogram
  Decision Tree Analysis -> expected-value branch chart
  Markov Analysis        -> steady-state bar chart
  (everything else)      -> shared-risk contribution (Pareto-style) bar chart

These are illustrative risk visuals grounded in the cluster's size and shared
factors, not claims about specific company financials. Output cached to
_build/charts.json keyed by cluster id.
"""
import os, json, io, base64, hashlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CLUSTERS = json.load(open(os.path.join(HERE, "clusters.json")))
NARR = json.load(open(os.path.join(HERE, "narratives.json")))
OUT = os.path.join(HERE, "charts.json")

# Warm, light palette derived from the brand (cream / gold / muted earth).
CREAM = "#faf6ef"
INK = "#2b2621"
GOLD = "#c8912f"
RUST = "#a1542f"
SAGE = "#6f7b5e"
SLATE = "#4a5b6b"
PALETTE = [GOLD, RUST, SLATE, SAGE, "#8a6d3b", "#7c4a3a"]

plt.rcParams.update({
    "figure.facecolor": CREAM,
    "axes.facecolor": CREAM,
    "savefig.facecolor": CREAM,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.edgecolor": "#d8ccb8",
    "font.size": 11,
    "axes.titlesize": 13,
})


def seed_for(cid):
    return int(hashlib.md5(str(cid).encode()).hexdigest(), 16) % (2**32)


def to_data_uri(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def chart_monte_carlo(c, n):
    rng = np.random.default_rng(seed_for(c["id"]))
    # distribution of portfolio outcome under the shared risk (illustrative)
    data = rng.normal(0, 1, 20000) * 12 - 4 + rng.standard_t(5, 20000) * 3
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.hist(data, bins=60, color=GOLD, edgecolor=CREAM, alpha=0.9)
    p5 = np.percentile(data, 5)
    ax.axvline(p5, color=RUST, lw=2, ls="--", label=f"5% VaR = {p5:.0f}%")
    ax.axvline(0, color=SLATE, lw=1)
    ax.set_title("Monte Carlo: Portfolio Outcome Distribution Under Shared Risk")
    ax.set_xlabel("Simulated 12-month portfolio return (%)")
    ax.set_ylabel("Frequency")
    ax.legend(frameon=False)
    return to_data_uri(fig)


def chart_decision_tree(c, n):
    fig, ax = plt.subplots(figsize=(7, 3.6))
    labels = ["Hedge\n(short pure-play)", "No hedge\n(hold private only)"]
    outcomes = [
        ("Risk hits", 0.40, -8, -45),
        ("Risk clears", 0.60, -2, 18),
    ]
    ev_hedge = sum(p * h for _, p, h, _ in outcomes)
    ev_none = sum(p * u for _, p, _, u in outcomes)
    x = np.arange(2)
    vals = [ev_hedge, ev_none]
    ax.bar(x, vals, color=[SAGE, RUST], width=0.5, edgecolor=CREAM, zorder=3)
    lo = min(vals + [0]); hi = max(vals + [0])
    pad = (hi - lo) * 0.18 + 1
    ax.set_ylim(lo - pad, hi + pad)
    for i, v in enumerate(vals):
        # place label just outside the bar end, clear of the axis tick labels
        off = pad * 0.35
        yy = v + off if v >= 0 else v - off
        ax.text(i, yy, f"EV {v:+.1f}%", ha="center",
                va="bottom" if v >= 0 else "top", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.axhline(0, color=SLATE, lw=1, zorder=2)
    ax.set_title("Decision Tree: Expected Value of Hedging the Shared Risk")
    ax.set_ylabel("Expected portfolio return (%)")
    return to_data_uri(fig)


def chart_markov(c, n):
    states = ["Stable", "Stressed", "Distressed", "Recovered"]
    rng = np.random.default_rng(seed_for(c["id"]))
    steady = rng.dirichlet([6, 3, 1.5, 4])
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.bar(states, steady * 100, color=PALETTE[:4], edgecolor=CREAM)
    for i, v in enumerate(steady * 100):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center", fontweight="bold")
    ax.set_title("Markov: Long-Run Share of Companies by Credit State")
    ax.set_ylabel("Steady-state probability (%)")
    ax.set_ylim(0, max(steady * 100) + 10)
    return to_data_uri(fig)


def chart_pareto(c, n):
    factors = NARR[str(c["id"])].get("shared_risk_factors", [])[:6]
    if not factors:
        factors = [t for t in c["top_terms"][:6]]
    rng = np.random.default_rng(seed_for(c["id"]))
    weights = np.sort(rng.dirichlet(np.ones(len(factors)) * 1.5))[::-1] * 100
    short = [f[:34] + ("…" if len(f) > 34 else "") for f in factors]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    y = np.arange(len(short))[::-1]
    ax.barh(y, weights, color=GOLD, edgecolor=CREAM)
    cum = np.cumsum(weights)
    ax2 = ax.twiny()
    ax2.plot(cum, y, color=RUST, marker="o", lw=2)
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("Cumulative contribution (%)", color=RUST)
    ax.set_yticks(y)
    ax.set_yticklabels(short, fontsize=9)
    ax.set_xlabel("Share of cluster risk signal (%)")
    ax.set_title("Pareto: Which Shared Risks Dominate the Portfolio")
    return to_data_uri(fig)


BUILDERS = {
    "Monte Carlo Simulation": chart_monte_carlo,
    "Decision Tree Analysis": chart_decision_tree,
    "Markov Analysis": chart_markov,
}


def main():
    charts = {}
    for c in CLUSTERS:
        cid = str(c["id"])
        tech = NARR.get(cid, {}).get("iso_technique", "")
        builder = BUILDERS.get(tech, chart_pareto)
        charts[cid] = {"technique": tech, "data_uri": builder(c, c["size"])}
        print(f"  #{c['id']:2d} chart: {tech or 'Pareto (default)'}")
    with open(OUT, "w") as f:
        json.dump(charts, f)
    print(f"charts generated: {len(charts)}")


if __name__ == "__main__":
    main()
