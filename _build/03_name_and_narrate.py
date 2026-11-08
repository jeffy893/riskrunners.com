#!/usr/bin/env python3
"""
Step 3 — Use Bedrock (Claude Haiku 4.5) to name each portfolio and write its
Event Horizon narrative.

Only the COMPACT cluster summary is sent (top terms + a dozen representative
companies + ~14 representative factor sentences), never the full corpus. One
call per cluster (~30 calls). Results are cached to _build/narratives.json so
re-runs are free and the job is resumable if interrupted.

Output: _build/narratives.json  (keyed by cluster id)
"""
import os, json, time, sys
import boto3
from botocore.config import Config

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, "clusters.json")
OUT = os.path.join(HERE, "narratives.json")

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-west-2"

client = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
    config=Config(retries={"max_attempts": 6, "mode": "adaptive"},
                  read_timeout=120, connect_timeout=15),
)

SYSTEM = (
    "You are a risk analyst for Pure Play (riskrunners.com), applying ISO 31010 "
    "risk-management methods to publicly traded companies. The data is a cluster "
    "of companies from 2019 SEC 10-K Item 1A filings that share the same risk "
    "factors. The business thesis: a company with the same risk factors as a "
    "private investment is a PURE PLAY hedge. If you own private equity in a car "
    "wash, shorting a public car-wash company with identical risk factors hedges "
    "your downside, because the same event that hurts your private holding hurts "
    "the public one. Each cluster is therefore a hedgeable PORTFOLIO of companies "
    "that move together when a shared risk materializes.\n\n"
    "Write for a sophisticated investor. Be concrete, grounded in the actual risk "
    "factors shown. Do not invent company names or ticker symbols. Use only the "
    "companies provided. Output STRICT JSON, no markdown fences."
)

PROMPT_TMPL = """Here is one portfolio cluster.

TOP DISTINGUISHING TERMS:
{terms}

REPRESENTATIVE COMPANIES (closest to the cluster center):
{companies}

REPRESENTATIVE RISK-FACTOR SENTENCES (verbatim from the filings):
{factors}

Total companies in this portfolio: {size}

Produce a JSON object with EXACTLY these keys:
{{
  "name": "A short, evocative portfolio name (3-6 words). Example style: 'Interest-Rate-Sensitive Construction Cyclicals', 'Clinical-Trial Binary Outcomes', 'Commodity Input Squeeze'. No company names.",
  "tagline": "One sentence (<=160 chars) stating the shared risk thesis.",
  "event_horizon": "2-3 sentences describing the decision point / event horizon: what real-world event would materialize this cluster's shared risk, and why these companies move together. Reference the pure-play hedging logic.",
  "shared_risk_factors": ["5-7 bullet strings, each a distinct shared risk theme present across the cluster, phrased crisply"],
  "hedge_thesis": "2-3 sentences: how an investor would use this portfolio as a pure-play hedge (what private exposure it mirrors, long/short framing).",
  "news_signals": ["4-6 short 'what to watch in the news' event signals that would move this portfolio, e.g. 'Fed rate decisions', 'FDA advisory committee votes'"],
  "iso_technique": "The single most illuminating ISO 31010 technique for THIS cluster's risk structure (choose from: Bow Tie Analysis, Decision Tree Analysis, Monte Carlo Simulation, Game Theory, Layers of Protection Analysis, Ishikawa Fishbone, Pareto Analysis, Cross Impact Analysis, Cost-Benefit Analysis, Markov Analysis). Pick the best fit for the dominant uncertainty.",
  "iso_rationale": "1-2 sentences on why that technique fits this cluster."
}}

Return ONLY the JSON object."""


def build_prompt(c):
    companies = "\n".join(f"- {m['company']}" for m in c["rep_companies"])
    factors = "\n".join(f"- {s}" for s in c["rep_factors"])
    return PROMPT_TMPL.format(
        terms=", ".join(c["top_terms"]),
        companies=companies,
        factors=factors,
        size=c["size"],
    )


def call(prompt):
    resp = client.converse(
        modelId=MODEL_ID,
        system=[{"text": SYSTEM}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 1400, "temperature": 0.4},
    )
    return resp["output"]["message"]["content"][0]["text"].strip()


def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def main():
    with open(IN, encoding="utf-8") as f:
        clusters = json.load(f)

    cache = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            cache = json.load(f)

    for c in clusters:
        cid = str(c["id"])
        if cid in cache and cache[cid].get("name"):
            print(f"  cached #{c['id']}: {cache[cid]['name']}")
            continue
        prompt = build_prompt(c)
        for attempt in range(4):
            try:
                raw = call(prompt)
                obj = parse_json(raw)
                assert obj.get("name"), "missing name"
                cache[cid] = obj
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False)
                print(f"  #{c['id']:2d} (n={c['size']}): {obj['name']}  [{obj.get('iso_technique','?')}]")
                break
            except Exception as e:
                wait = 2 ** attempt
                print(f"  #{c['id']} attempt {attempt+1} failed: {str(e)[:120]}; retry in {wait}s", file=sys.stderr)
                time.sleep(wait)
        else:
            print(f"  #{c['id']} FAILED after retries", file=sys.stderr)

    print(f"\nnarratives ready: {len([k for k,v in cache.items() if v.get('name')])}/{len(clusters)}")


if __name__ == "__main__":
    main()
