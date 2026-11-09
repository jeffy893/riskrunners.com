#!/usr/bin/env python3
"""
Step 3b — For each portfolio, use Bedrock (Claude Haiku 4.5) to:

  (a) define 6-9 NAMED risk themes grounded in the cluster's ACTUAL risk-factor
      language, each with concrete lexical cues (lowercase keywords/phrases that
      actually occur in these filings) used later to measure real prevalence;
  (b) choose the single ISO 31010 technique that the TEXT can honestly support
      for this portfolio — restricted to techniques that need no fabricated
      numbers:
        - "Bow Tie Analysis"        (qualitative cause -> event -> consequence)
        - "Ishikawa (Fishbone)"     (qualitative root-cause categories)
        - "Risk-Theme Prevalence"   (real counts: how many companies disclose each theme)
        - "Cross Impact Analysis"   (real co-occurrence of themes across companies)
      Monte Carlo / Decision Tree / Markov are intentionally excluded because the
      filings contain no probabilities, returns, or transition rates to compute
      them from.

The themes + cues are the bridge to REAL numbers: step 3c matches every member
company's actual factor sentences against these cues (local, deterministic) to
produce genuine prevalence and co-occurrence. No numbers are invented here.

Output: _build/themes.json  (keyed by cluster id), cached/resumable.
"""
import os, json, re, time, sys
import boto3
from botocore.config import Config

HERE = os.path.dirname(os.path.abspath(__file__))
CLUSTERS = json.load(open(os.path.join(HERE, "clusters.json")))
NARR = json.load(open(os.path.join(HERE, "narratives.json")))
RECORDS = json.load(open(os.path.join(HERE, "risk_factors.json")))
OUT = os.path.join(HERE, "themes.json")

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-west-2"
client = boto3.client("bedrock-runtime", region_name=REGION,
                      config=Config(retries={"max_attempts": 6, "mode": "adaptive"},
                                    read_timeout=120, connect_timeout=15))

REC_BY_SLUG = {r["slug"]: r for r in RECORDS}

SYSTEM = (
    "You are a risk analyst for Pure Play (riskrunners.com) applying ISO 31010 "
    "methods to clusters of publicly traded companies that share risk factors in "
    "their 2019 SEC 10-K filings. You must stay strictly grounded in the actual "
    "risk-factor text provided. Never invent probabilities, dollar figures, or "
    "statistics — this analysis uses only what the text supports. Output STRICT "
    "JSON, no markdown fences."
)

PROMPT = """PORTFOLIO: {name}
THESIS: {tagline}
TOP DISTINGUISHING TERMS: {terms}

REAL RISK-FACTOR SENTENCES sampled from companies in this portfolio (verbatim):
{factors}

Define the risk structure of THIS portfolio, grounded only in the text above.

Return a JSON object with EXACTLY these keys:
{{
  "themes": [
     {{
       "name": "Short GENERAL theme name (2-4 words) that applies across the WHOLE portfolio, e.g. 'Client concentration', 'Raw-material cost inflation', 'Interest-rate sensitivity'. NEVER name a specific company, product, or ticker — themes must generalize to many filings.",
       "cues": ["8-14 SHORT lowercase cues (1-3 words each, NOT full sentences) that recur in filings of this risk type and let a simple keyword match detect the theme. Prefer general domain terms over verbatim phrases: e.g. 'client concentration', 'contract renewal', 'key customer', 'revenue concentration'. No company names. Lowercase."]
     }}
     // 6 to 9 themes, covering the distinct risks visible in the text. Each theme must plausibly apply to a LARGE share of the portfolio, not one company.
  ],
  "technique": "Choose the ONE ISO 31010 technique the text best supports, from EXACTLY this set: 'Bow Tie Analysis', 'Ishikawa (Fishbone)', 'Risk-Theme Prevalence', 'Cross Impact Analysis'. Pick 'Bow Tie Analysis' when there is a clear single central risk event with identifiable causes and consequences; 'Ishikawa (Fishbone)' when the risk is driven by several independent root-cause categories; 'Risk-Theme Prevalence' when the portfolio is best understood by WHICH risks dominate across its members; 'Cross Impact Analysis' when the interesting feature is how multiple risks reinforce each other.",
  "technique_rationale": "1-2 sentences: why this technique fits THIS portfolio's risk structure, referencing the themes.",
  "central_event": "For Bow Tie: the single central risk event (short phrase). For others: the dominant shared risk (short phrase).",
  "causes": ["3-5 short cause/trigger phrases drawn from the themes (what makes the central risk fire)"],
  "consequences": ["3-5 short consequence phrases (what happens to these companies when it fires)"]
}}
Return ONLY the JSON object."""


def sample_factors(cluster, k=38):
    """Richer verbatim sample than the 14 kept in clusters.json: pull from the
    cluster's representative companies' full factor lists."""
    out, seen = [], set()
    for m in cluster["rep_companies"]:
        rec = REC_BY_SLUG.get(m["slug"])
        if not rec:
            continue
        for f in rec["factors"]:
            key = f[:50].lower()
            if key in seen:
                continue
            if len(f) < 25:
                continue
            out.append(f)
            seen.add(key)
            if len(out) >= k:
                return out
    return out


def call(prompt):
    r = client.converse(
        modelId=MODEL_ID, system=[{"text": SYSTEM}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 1600, "temperature": 0.3},
    )
    return r["output"]["message"]["content"][0]["text"].strip()


def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    s, e = text.find("{"), text.rfind("}")
    return json.loads(text[s:e + 1])


def main():
    cache = {}
    if os.path.exists(OUT):
        cache = json.load(open(OUT))

    for c in CLUSTERS:
        cid = str(c["id"])
        if cid in cache and cache[cid].get("themes"):
            print(f"  cached #{c['id']}: {len(cache[cid]['themes'])} themes, {cache[cid]['technique']}")
            continue
        narr = NARR[cid]
        facts = sample_factors(c)
        prompt = PROMPT.format(
            name=narr["name"], tagline=narr.get("tagline", ""),
            terms=", ".join(c["top_terms"]),
            factors="\n".join(f"- {s}" for s in facts),
        )
        for attempt in range(4):
            try:
                obj = parse_json(call(prompt))
                assert obj.get("themes") and obj.get("technique"), "missing keys"
                # normalize cues lowercase
                for t in obj["themes"]:
                    t["cues"] = [str(x).lower().strip() for x in t.get("cues", []) if str(x).strip()]
                cache[cid] = obj
                json.dump(cache, open(OUT, "w"), ensure_ascii=False)
                print(f"  #{c['id']:2d}  {obj['technique']:22s}  {len(obj['themes'])} themes  "
                      f"[{', '.join(t['name'] for t in obj['themes'][:3])}…]")
                break
            except Exception as ex:
                w = 2 ** attempt
                print(f"  #{c['id']} attempt {attempt+1}: {str(ex)[:110]}; retry {w}s", file=sys.stderr)
                time.sleep(w)
        else:
            print(f"  #{c['id']} FAILED", file=sys.stderr)

    done = len([v for v in cache.values() if v.get("themes")])
    print(f"\nthemes ready: {done}/{len(CLUSTERS)}")
    # technique distribution
    from collections import Counter
    cnt = Counter(v["technique"] for v in cache.values() if v.get("technique"))
    for t, n in cnt.most_common():
        print(f"   {n:3d}  {t}")


if __name__ == "__main__":
    main()
