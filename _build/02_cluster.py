#!/usr/bin/env python3
"""
Step 2 — Cluster companies into risk-theme portfolios.

Pure-play thesis: companies that share the SAME risk factors move together, so a
cluster is a hedgeable portfolio. We TF-IDF each company's risk-factor document,
KMeans into N clusters, then summarise each cluster compactly (top terms +
representative companies + representative factor sentences). The compact summary
is what gets sent to Bedrock later — never the full 311K sentences.

Output: _build/clusters.json
"""
import os, json, re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, "risk_factors.json")
OUT = os.path.join(HERE, "clusters.json")

N_CLUSTERS = 30
TOP_TERMS = 18
REP_COMPANIES = 12      # representative companies kept per cluster for the LLM
REP_FACTORS = 14        # representative factor sentences kept per cluster
SEED = 42

# Boilerplate terms that appear in nearly every 10-K and carry no signal.
STOP_EXTRA = {
    "risk", "risks", "factors", "may", "could", "would", "affect", "affected",
    "adversely", "material", "materially", "business", "results", "operations",
    "financial", "condition", "company", "companies", "our", "us", "we",
    "including", "result", "results", "ability", "able", "operating", "item",
    "additional", "future", "cause", "significant", "significantly", "effect",
    "impact", "subject", "related", "certain", "make", "time", "make",
}


def main():
    with open(IN, encoding="utf-8") as f:
        records = json.load(f)

    docs = [" ".join(r["factors"]) for r in records]

    vec = TfidfVectorizer(
        max_features=6000,
        ngram_range=(1, 2),
        min_df=5,
        max_df=0.55,
        stop_words=list(STOP_EXTRA) + ["english"] if False else "english",
        sublinear_tf=True,
    )
    X = vec.fit_transform(docs)
    terms = np.array(vec.get_feature_names_out())

    km = KMeans(n_clusters=N_CLUSTERS, random_state=SEED, n_init=10)
    labels = km.fit_predict(X)

    centroids = km.cluster_centers_

    clusters = []
    for c in range(N_CLUSTERS):
        idx = np.where(labels == c)[0]
        if len(idx) == 0:
            continue

        # top terms by centroid weight, filtered against boilerplate
        order = centroids[c].argsort()[::-1]
        top_terms = []
        for t in order:
            term = terms[t]
            if any(w in STOP_EXTRA for w in term.split()):
                continue
            top_terms.append(term)
            if len(top_terms) >= TOP_TERMS:
                break

        # representative companies: closest to centroid
        sims = cosine_similarity(X[idx], centroids[c].reshape(1, -1)).ravel()
        rep_order = idx[sims.argsort()[::-1]]
        rep_company_recs = [records[i] for i in rep_order[:REP_COMPANIES]]
        rep_companies = [
            {"company": r["company"], "slug": r["slug"]}
            for r in rep_company_recs
        ]

        # full membership list (name + slug), alphabetical
        members = sorted(
            ({"company": records[i]["company"], "slug": records[i]["slug"]}
             for i in idx),
            key=lambda m: m["company"],
        )

        # representative factor sentences: pull from the closest companies,
        # pick sentences that contain top terms, dedup-ish
        rep_factors = []
        seen = set()
        termset = set(" ".join(top_terms).split())
        for r in rep_company_recs:
            for fct in r["factors"]:
                key = fct[:60].lower()
                if key in seen:
                    continue
                words = set(re.findall(r"[a-z]+", fct.lower()))
                if termset & words:
                    rep_factors.append(fct)
                    seen.add(key)
                if len(rep_factors) >= REP_FACTORS:
                    break
            if len(rep_factors) >= REP_FACTORS:
                break

        clusters.append({
            "id": c,
            "size": int(len(idx)),
            "top_terms": top_terms,
            "rep_companies": rep_companies,
            "rep_factors": rep_factors,
            "members": members,
        })

    clusters.sort(key=lambda c: c["size"], reverse=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(clusters, f, ensure_ascii=False)

    print(f"clusters: {len(clusters)}  (companies: {len(records)})")
    for c in clusters:
        print(f"  #{c['id']:2d}  n={c['size']:4d}  {', '.join(c['top_terms'][:8])}")


if __name__ == "__main__":
    main()
