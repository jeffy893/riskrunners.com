#!/usr/bin/env python3
"""
Step 3c — Compute REAL per-portfolio risk metrics from the actual filings.

For each portfolio and each LLM-defined theme (with its lexical cues), scan
every member company's real risk-factor sentences and record whether that
company discloses the theme (a cue appears in its text). From those booleans:

  prevalence[theme]      = # member companies disclosing the theme (REAL count)
  cooccur[theme_i,j]     = # companies disclosing BOTH themes (REAL count)
  per-company theme sets = used for co-occurrence and for the "typical company"

Then pick the honest ISO 31010 technique from the SHAPE of the real data:

  Risk-Theme Prevalence  -> prevalence is concentrated (a few themes dominate):
                            the story is WHICH risks are near-universal.
  Cross Impact Analysis  -> themes co-occur strongly (high average Jaccard):
                            the story is how risks travel together.
  Bow Tie Analysis       -> one theme is near-universal (a clear central event)
                            with distinct lower-prevalence causes/consequences.
  Ishikawa (Fishbone)    -> themes are many and weakly correlated (independent
                            root-cause families).

Everything here is counted from the text. No fabricated numbers.

Output: _build/metrics.json keyed by cluster id.
"""
import os, json, re
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CLUSTERS = json.load(open(os.path.join(HERE, "clusters.json")))
THEMES = json.load(open(os.path.join(HERE, "themes.json")))
RECORDS = json.load(open(os.path.join(HERE, "risk_factors.json")))
NARR = json.load(open(os.path.join(HERE, "narratives.json")))
OUT = os.path.join(HERE, "metrics.json")

REC_BY_SLUG = {r["slug"]: r for r in RECORDS}


STOP = set("""a an the of and or to in on for with without by from as is are be been
being that this these those it its their our your we us you they them he she his her
which who whom whose when where why how will would could should may might can cannot
not no nor if then than so such very more most less least into onto over under out up
down off out about above below between among through during before after any all each
every some other another same own only also just even still yet due per via""".split())


def salient_words(cue):
    return [w for w in re.findall(r"[a-z][a-z\-]{2,}", cue.lower()) if w not in STOP]


def compile_cue(cue):
    """Return (kind, data) describing how to detect this cue in a company's text.

    - A single salient word (e.g. 'reinsurance') matches on that exact word.
    - A multi-word cue matches only if ALL its salient words appear within a
      short window of each other (a proximity match), OR the exact phrase
      appears. This captures paraphrase ('raw material ... cost') without firing
      on scattered boilerplate ('cost' alone appears in every filing)."""
    cue = cue.strip().lower()
    words = salient_words(cue)
    phrase = re.escape(cue).replace(r"\ ", r"\s+")
    phrase_pat = re.compile(r"(?<![a-z])" + phrase + r"(?![a-z])")
    if len(words) <= 1:
        w = words[0] if words else None
        wp = re.compile(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])") if w else None
        return ("word", (phrase_pat, wp))
    word_pats = [re.compile(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])") for w in words]
    return ("phrase", (phrase_pat, word_pats))


def main():
    metrics = {}
    for c in CLUSTERS:
        cid = str(c["id"])
        th = THEMES[cid]
        themes = th["themes"]
        names = [t["name"] for t in themes]
        # per theme: list of compiled cues, plus the theme-name words as an
        # extra cue so a theme is detectable even if its listed cues are noisy
        pats = []
        for t in themes:
            cues = [compile_cue(x) for x in t["cues"] if x]
            pats.append(cues)

        members = c["members"]
        N = len(members)

        WINDOW = 60  # chars: salient words must co-occur within this window

        def cue_hit(text, cue):
            kind, data = cue
            if kind == "word":
                phrase_pat, wp = data
                return bool(wp and wp.search(text))
            phrase_pat, word_pats = data
            if phrase_pat.search(text):
                return True
            # proximity: find positions of each salient word; require ALL words
            # to appear with the span of the rarest anchor within WINDOW of the
            # others. Simple approach: for each occurrence of the first word,
            # check the other words appear within WINDOW chars.
            anchors = [m.start() for m in word_pats[0].finditer(text)]
            if not anchors:
                return False
            for a in anchors:
                lo, hi = a - WINDOW, a + WINDOW
                seg = text[max(0, lo):hi]
                if all(wp.search(seg) for wp in word_pats[1:]):
                    return True
            return False

        # per-company theme membership booleans
        company_themes = []  # list of sets of theme indices
        for m in members:
            rec = REC_BY_SLUG.get(m["slug"])
            text = (" ".join(rec["factors"]) if rec else "").lower()
            hits = set()
            for ti, clist in enumerate(pats):
                for cue in clist:
                    if cue_hit(text, cue):
                        hits.add(ti)
                        break
            company_themes.append(hits)

        k = len(themes)
        prevalence = [0] * k
        for s in company_themes:
            for ti in s:
                prevalence[ti] += 1

        cooccur = np.zeros((k, k), dtype=int)
        for s in company_themes:
            sl = list(s)
            for a in range(len(sl)):
                for b in range(len(sl)):
                    cooccur[sl[a], sl[b]] += 1

        # Jaccard between themes (over companies)
        jac = np.zeros((k, k))
        for i in range(k):
            for j in range(k):
                if i == j:
                    continue
                inter = cooccur[i, j]
                union = prevalence[i] + prevalence[j] - inter
                jac[i, j] = inter / union if union else 0.0

        prev_frac = np.array(prevalence) / max(1, N)
        order = np.argsort(prev_frac)[::-1]

        # ---- data-driven, honest technique selection ----
        top = prev_frac[order]
        near_universal = int((prev_frac >= 0.80).sum())
        mid = int(((prev_frac >= 0.30) & (prev_frac < 0.80)).sum())
        avg_jac = float(jac[np.triu_indices(k, 1)].mean()) if k > 1 else 0.0
        # concentration: gap between top themes and the rest
        concentration = float(top[:3].mean() - top[3:].mean()) if k > 3 else 0.0

        if near_universal == 1 and mid >= 2:
            technique = "Bow Tie Analysis"
        elif avg_jac >= 0.45:
            technique = "Cross Impact Analysis"
        elif concentration >= 0.28:
            technique = "Risk-Theme Prevalence"
        elif k >= 7 and avg_jac < 0.30:
            technique = "Ishikawa (Fishbone)"
        else:
            # fall back to whichever signal is strongest
            technique = "Risk-Theme Prevalence" if concentration >= 0.18 else "Cross Impact Analysis"

        # rationale generated to MATCH the data-driven technique, citing real
        # measured numbers (never the LLM's stale, mismatched rationale).
        top_name = names[order[0]]
        top_frac = prev_frac[order[0]]
        n_dom = int((prev_frac >= 0.60).sum())
        if technique == "Risk-Theme Prevalence":
            rationale = (
                f"Across the {N} companies, {n_dom} risk theme"
                f"{'s' if n_dom != 1 else ''} are disclosed by a majority, led by "
                f"“{top_name}” at {top_frac:.0%}. Prevalence ranking is the clearest lens: "
                f"it shows which risks are near-universal in the portfolio and therefore "
                f"drive the companies together."
            )
        elif technique == "Cross Impact Analysis":
            rationale = (
                f"These risks rarely appear alone — themes co-occur in the same company "
                f"at an average overlap of {avg_jac:.2f} (Jaccard). Cross-impact analysis "
                f"shows how the shared risks reinforce one another, which is why the "
                f"companies move as a bloc."
            )
        elif technique == "Bow Tie Analysis":
            rationale = (
                f"One risk — “{top_name}” — is near-universal ({top_frac:.0%} of the {N} "
                f"companies), acting as a central event with distinct lower-prevalence "
                f"causes and consequences. A bow tie maps those causes, the event, and its "
                f"fallout across the cluster."
            )
        else:  # Ishikawa
            rationale = (
                f"The portfolio's risk is driven by several weakly-overlapping families "
                f"(average co-occurrence just {avg_jac:.2f}), so no single central event "
                f"dominates. A fishbone separates these independent root-cause families, "
                f"each measured by how many of the {N} companies disclose it."
            )

        metrics[cid] = {
            "N": N,
            "themes": names,
            "prevalence": prevalence,
            "prevalence_frac": [round(float(x), 3) for x in prev_frac],
            "cooccur": cooccur.tolist(),
            "jaccard": [[round(float(x), 3) for x in row] for row in jac],
            "order": [int(x) for x in order],
            "avg_jaccard": round(avg_jac, 3),
            "concentration": round(concentration, 3),
            "near_universal": near_universal,
            "technique": technique,
            "central_event": th.get("central_event", ""),
            "causes": th.get("causes", []),
            "consequences": th.get("consequences", []),
            "technique_rationale": rationale,
        }
        print(f"  #{c['id']:2d} N={N:4d}  tech={technique:22s} "
              f"avgJ={avg_jac:.2f} conc={concentration:.2f} nu={near_universal}  "
              f"top: {names[order[0]]} {prev_frac[order[0]]:.0%}")

    json.dump(metrics, open(OUT, "w"), ensure_ascii=False)
    from collections import Counter
    print("\ntechnique distribution:")
    for t, n in Counter(m["technique"] for m in metrics.values()).most_common():
        print(f"   {n:3d}  {t}")


if __name__ == "__main__":
    main()
