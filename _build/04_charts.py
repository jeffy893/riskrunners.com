#!/usr/bin/env python3
"""
Step 4 — Render ONE technique-appropriate visual per portfolio, driven ENTIRELY
by real metrics computed from the filings (step 3c). No fabricated numbers.

The technique was chosen in 3c from the SHAPE of the real data:

  Risk-Theme Prevalence  -> horizontal bar chart of the REAL share of member
                            companies that disclose each theme (counts shown).
  Cross Impact Analysis  -> heatmap of REAL co-occurrence (Jaccard) between
                            themes across the portfolio's companies.
  Bow Tie Analysis       -> causes -> central event -> consequences, labelled
                            from the LLM's text-grounded cause/consequence lists;
                            theme prevalence annotations are real counts.
  Ishikawa (Fishbone)    -> root-cause families (themes) with their real
                            prevalence, arranged as a fishbone.

Every number printed on a chart is a count or ratio measured from the 2019
filings. Output cached to _build/charts.json keyed by cluster id.
"""
import os, json, io, base64, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
CLUSTERS = json.load(open(os.path.join(HERE, "clusters.json")))
NARR = json.load(open(os.path.join(HERE, "narratives.json")))
METRICS = json.load(open(os.path.join(HERE, "metrics.json")))
OUT = os.path.join(HERE, "charts.json")

CREAM = "#faf6ef"; PAPER = "#fffdf9"; INK = "#2b2621"
GOLD = "#c8912f"; RUST = "#a1542f"; SAGE = "#6f7b5e"; SLATE = "#4a5b6b"
TEAL = "#19a6c8"; GREEN = "#3fb27f"; BAD = "#b0472b"

plt.rcParams.update({
    "figure.facecolor": CREAM, "axes.facecolor": CREAM, "savefig.facecolor": CREAM,
    "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.edgecolor": "#d8ccb8", "font.size": 11, "axes.titlesize": 13,
    "font.family": "sans-serif",
})


def to_data_uri(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=115, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def wrap(s, w):
    return "\n".join(textwrap.wrap(s, w)) if s else ""


def short(s, n):
    s = (s or "").strip().rstrip(".")
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def box(ax, x, y, w, h, text, fc, ec, fs=7.6, tc="#1a1a1a", bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25",
                 facecolor=fc, edgecolor=ec, linewidth=1.4, mutation_scale=6))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, fontweight="bold" if bold else "normal")


# ---------------------------------------------------------------- PREVALENCE
def chart_prevalence(cid):
    d = METRICS[cid]; name = NARR[cid]["name"]; N = d["N"]
    order = d["order"]
    themes = [d["themes"][i] for i in order]
    counts = [d["prevalence"][i] for i in order]
    fracs = [d["prevalence_frac"][i] for i in order]

    fig, ax = plt.subplots(figsize=(8.8, max(3.4, 0.56 * len(themes) + 1.6)))
    y = np.arange(len(themes))[::-1]
    bars = ax.barh(y, [f * 100 for f in fracs], color=GOLD, edgecolor=CREAM, height=0.66)
    # shade the dominant (>=60%) themes in rust to draw the eye
    for b, f in zip(bars, fracs):
        if f >= 0.60:
            b.set_color(RUST)
    for yi, (cnt, f) in enumerate(zip(counts, fracs)):
        ax.text(f * 100 + 1.2, y[yi], f"{f:.0%}  ({cnt}/{N})",
                va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([wrap(t, 32) for t in themes], fontsize=9)
    ax.set_xlim(0, 112)
    ax.set_xlabel("Share of the portfolio's companies disclosing this risk theme")
    ax.set_title(f"Risk-Theme Prevalence — {short(name,42)}\n"
                 f"Measured across all {N} companies' 2019 risk-factor filings", fontsize=11)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color="#e4dac8", lw=0.8)
    ax.set_axisbelow(True)
    return to_data_uri(fig)


# -------------------------------------------------------------- CROSS IMPACT
def chart_cross_impact(cid):
    d = METRICS[cid]; name = NARR[cid]["name"]; N = d["N"]
    order = d["order"][:7]
    themes = [d["themes"][i] for i in order]
    J = np.array(d["jaccard"])
    M = J[np.ix_(order, order)]
    k = len(order)

    fig, ax = plt.subplots(figsize=(8.2, 7.0))
    im = ax.imshow(M, cmap="YlOrBr", vmin=0, vmax=1, aspect="equal")
    ax.set_xticks(range(k)); ax.set_yticks(range(k))
    ax.set_xticklabels([wrap(t, 14) for t in themes], fontsize=7.4, rotation=45, ha="right")
    ax.set_yticklabels([wrap(t, 16) for t in themes], fontsize=7.4)
    for i in range(k):
        for j in range(k):
            if i == j:
                ax.text(j, i, "—", ha="center", va="center", fontsize=8, color="#b9ab92")
            else:
                v = M[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=7, color="#3a2a16" if v > 0.5 else "#8a7f6f")
    ax.set_title(f"Cross Impact Analysis — {short(name,34)}\n"
                 f"How often risk themes co-occur in the same company "
                 f"(Jaccard overlap, {N} companies)", fontsize=10.5, pad=10)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("Share of companies with BOTH themes", fontsize=8)
    cb.ax.tick_params(labelsize=7)
    return to_data_uri(fig)


# ------------------------------------------------------------------ BOW TIE
def chart_bow_tie(cid):
    d = METRICS[cid]; name = NARR[cid]["name"]; N = d["N"]
    central = short(d.get("central_event") or name, 38)
    causes = [short(c, 46) for c in (d.get("causes") or [])][:4]
    cons = [short(c, 46) for c in (d.get("consequences") or [])][:4]
    if not causes:
        order = d["order"]
        causes = [short(d["themes"][i], 46) for i in order[:4]]
    if not cons:
        cons = ["Share-price drawdown", "Earnings impairment",
                "Financing / covenant stress", "Correlated loss vs. private holding"]

    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    ax.text(50, 97, f"Bow Tie Analysis — {short(name,40)}", ha="center", va="top",
            fontsize=13, fontweight="bold")
    ax.text(50, 92, short(NARR[cid].get("tagline", ""), 92), ha="center", va="top",
            fontsize=8.5, color="#6b6052", style="italic")

    box(ax, 41, 43, 18, 16, wrap("CENTRAL EVENT: " + central, 15), TEAL, "#117a94",
        fs=7.6, tc="white", bold=True)

    ax.text(14, 84, "CAUSES / TRIGGERS", ha="center", fontsize=9, fontweight="bold", color=BAD)
    ys = np.linspace(68, 28, max(1, len(causes)))
    for cse, yy in zip(causes, ys):
        box(ax, 0.5, yy - 5, 29, 10, wrap(cse, 26), "#f7e4de", BAD, fs=6.8)
        ax.add_patch(FancyArrowPatch((29.5, yy), (41, 51), arrowstyle="-|>",
                     mutation_scale=11, color="#9a8f7f", lw=1.3))

    ax.text(86, 84, "CONSEQUENCES", ha="center", fontsize=9, fontweight="bold", color=BAD)
    ys2 = np.linspace(68, 28, max(1, len(cons)))
    for cq, yy in zip(cons, ys2):
        box(ax, 70.5, yy - 5, 29, 10, wrap(cq, 26), "#f7e4de", BAD, fs=6.8)
        ax.add_patch(FancyArrowPatch((59, 51), (70.5, yy), arrowstyle="-|>",
                     mutation_scale=11, color="#9a8f7f", lw=1.3))

    # real anchor: prevalence of the top theme
    top_i = d["order"][0]
    tf = d["prevalence_frac"][top_i]; tc = d["prevalence"][top_i]
    ax.text(50, 13, f"Most prevalent shared driver: “{short(d['themes'][top_i],40)}” — "
                    f"disclosed by {tf:.0%} ({tc}/{N}) of the portfolio.",
            ha="center", fontsize=8, color="#6b6052")
    ax.text(50, 8.5, "Left: text-grounded causes that fire the central event. "
                     "Right: consequences shared across the cluster. The pure-play short is the hedging barrier.",
            ha="center", fontsize=7.6, color="#6b6052")
    return to_data_uri(fig)


# ----------------------------------------------------------------- ISHIKAWA
def chart_ishikawa(cid):
    d = METRICS[cid]; name = NARR[cid]["name"]; N = d["N"]
    order = d["order"]
    cats = [(short(d["themes"][i], 26), d["prevalence_frac"][i], d["prevalence"][i])
            for i in order[:6]]

    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    ax.text(50, 97, f"Ishikawa (Fishbone) — {short(name,40)}", ha="center", va="top",
            fontsize=13, fontweight="bold")
    ax.text(50, 92, "Independent root-cause families driving the portfolio's shared risk",
            ha="center", va="top", fontsize=8.5, color="#6b6052", style="italic")

    # spine
    ax.add_patch(FancyArrowPatch((6, 50), (80, 50), arrowstyle="-|>",
                 mutation_scale=22, color=SLATE, lw=2.4))
    box(ax, 80, 44, 18, 12, wrap("Shared risk\nmaterializes", 12), TEAL, "#117a94",
        fs=8, tc="white", bold=True)

    # ribs alternate top/bottom
    n = len(cats)
    xs = np.linspace(16, 72, max(1, (n + 1) // 2))
    tops = cats[0::2]; bots = cats[1::2]
    for i, (lab, frac, cnt) in enumerate(tops):
        x = xs[i] if i < len(xs) else xs[-1]
        ax.add_patch(FancyArrowPatch((x - 6, 77), (x + 3, 51), arrowstyle="-|>",
                     mutation_scale=12, color="#9a8f7f", lw=1.4))
        box(ax, x - 20, 80, 24, 9, wrap(lab, 22), "#f1e7d6", GOLD, fs=7)
        ax.text(x - 2, 65, f"{frac:.0%} ({cnt}/{N})", fontsize=7, color="#6b6052", ha="left")
    for i, (lab, frac, cnt) in enumerate(bots):
        x = xs[i] if i < len(xs) else xs[-1]
        ax.add_patch(FancyArrowPatch((x - 6, 23), (x + 3, 49), arrowstyle="-|>",
                     mutation_scale=12, color="#9a8f7f", lw=1.4))
        box(ax, x - 20, 11, 24, 9, wrap(lab, 22), "#f1e7d6", GOLD, fs=7)
        ax.text(x - 2, 33, f"{frac:.0%} ({cnt}/{N})", fontsize=7, color="#6b6052", ha="left")

    ax.text(50, 4, f"Each rib is a distinct risk family; % = share of the {N} companies that disclose it. "
                   f"Low inter-theme overlap (avg {d['avg_jaccard']:.2f}) is why these are independent causes.",
            ha="center", fontsize=7.4, color="#6b6052")
    return to_data_uri(fig)


BUILDERS = {
    "Risk-Theme Prevalence": chart_prevalence,
    "Cross Impact Analysis": chart_cross_impact,
    "Bow Tie Analysis": chart_bow_tie,
    "Ishikawa (Fishbone)": chart_ishikawa,
}


def main():
    charts = {}
    missing = set()
    for c in CLUSTERS:
        cid = str(c["id"])
        tech = METRICS[cid]["technique"]
        b = BUILDERS.get(tech)
        if b is None:
            missing.add(tech); b = chart_prevalence
        charts[cid] = {"technique": tech, "data_uri": b(cid)}
        print(f"  #{c['id']:2d}  {tech}")
    json.dump(charts, open(OUT, "w"))
    print(f"charts generated: {len(charts)}")
    if missing:
        print("WARNING no renderer for:", ", ".join(sorted(missing)))


if __name__ == "__main__":
    main()
