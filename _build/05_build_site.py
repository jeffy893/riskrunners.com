#!/usr/bin/env python3
"""
Step 5 — Build the new Pure Play site from clusters + narratives + charts.

Produces (in the repo root):
  index.html                       home page + portfolio grid
  portfolios/<slug>.html           30 Event Horizon portfolio reports
  methodology.html                 methodology / how-it-works page (regenerated)
  assets/site.css                  shared styling (warm light theme)
  assets/app.js                    left-nav toggle + client-side search
  assets/search-index.json         search data (portfolios, companies, factors)

Every page shares the same shell: a collapsible left nav listing all 30
portfolios (grouped by sector family) and a search box. Pages are self-contained
except for the shared /assets files, which is correct for a multi-page site.
"""
import os, json, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CLUSTERS = json.load(open(os.path.join(HERE, "clusters.json")))
NARR = json.load(open(os.path.join(HERE, "narratives.json")))
CHARTS = json.load(open(os.path.join(HERE, "charts.json")))
METRICS = json.load(open(os.path.join(HERE, "metrics.json")))

PORT_DIR = os.path.join(ROOT, "portfolios")
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(PORT_DIR, exist_ok=True)
os.makedirs(ASSETS, exist_ok=True)

YEAR = 2026
BRAND = "Pure Play"

# ---- group portfolios into sector families for the nav dropdowns ----
FAMILY_RULES = [
    ("Financials & Credit", ["bank", "credit", "capital", "policyholder", "cre", "collateral", "mortgage"]),
    ("Healthcare & Life Sciences", ["clinical", "fda", "device", "generic", "reimbursement", "surgical"]),
    ("Energy & Commodities", ["commodity", "energy", "midstream", "upstream", "oil", "gas"]),
    ("Technology & Semiconductors", ["semiconductor", "software", "digital", "fabless", "patent"]),
    ("Consumer & Retail", ["retail", "fashion", "restaurant", "consumer", "housing", "homebuilder"]),
    ("Industrials & Infrastructure", ["cyclical", "raw material", "defense", "trucking", "infrastructure", "telecom", "broadcast", "professional services"]),
]


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s


def e(s):
    return html.escape(str(s), quote=True)


def clean_artifacts(s):
    """Undo the 2019 scraper's punctuation encodings in risk-factor text.

    Verified against the full corpus (every pattern is unambiguous there):
      dlra<digit>   -> $<digit>   (always precedes a number)
      <digit>prca   -> <digit>%   (always follows a number)
      <d>cmam<d>    -> <d>,<d>     (thousands separator, always between digits)
      dtta          -> .          (decimal point AND abbreviation period, e.g. 'No.')
      &quote        -> "
      &apos         -> '           (possessive: 'lenders &apos' -> "lenders'")
      apstas        -> 's          (older possessive artifact, belt-and-suspenders)
    Patterns are anchored to digits/literals so real words (tampering,
    windshield, Lincoln, quotations) are never touched."""
    if not s:
        return s
    s = s.replace("&quote", '"')
    s = re.sub(r"\s*&apos", "'", s)           # drop the space before the apostrophe
    s = re.sub(r"dlra(?=\d)", "$", s)
    s = re.sub(r"(?<=\d)cmam(?=\d)", ",", s)
    s = re.sub(r"(?<=\d)prca", "%", s)
    s = s.replace("dtta", ".")                # decimal or abbreviation period
    s = s.replace("apstas", "'s")
    # remove page-break debris spliced into a sentence by the scraper:
    #   "... income is lower 10 ______ [94]Table of Contents" etc.
    s = re.sub(r"\s*\d{1,3}\s*_{6,}\s*(?:\[\d+\])?\s*"
               r"(?:Table of Contents|Back to Contents)?", " ", s)
    s = re.sub(r"\[\d+\]\s*(?:Table of Contents|Back to Contents)", " ", s)
    s = re.sub(r"_{4,}", " ", s)
    s = re.sub(r"[ \t]{2,}", " ", s).strip()
    # Strip a leading ALL-CAPS risk-factor HEADING glued to the body sentence,
    # e.g. "OUR FUTURE REVENUE ... DECLINE Our future revenues will depend ...".
    # Keep the normal-case prose that follows.
    m = re.match(r"^([A-Z][A-Z0-9 ,.;/()&'\u2018\u2019\u201c\u201d\"\-]{24,}?)(?=[A-Z][a-z])", s)
    if m and len(s) - len(m.group(1)) >= 40:
        s = s[len(m.group(1)):].strip()
    # tidy any doubled spaces introduced
    s = re.sub(r"[ \t]{2,}", " ", s).strip()
    return s


def looks_like_cruft(s):
    """True if a representative sentence is still unusable after cleaning:
    too short, residual TOC/underscore debris, a bare page number, or an
    ALL-CAPS heading line rather than prose."""
    if len(s) < 40:
        return True
    if "Table of Contents" in s or "Back to Contents" in s or "____" in s:
        return True
    if re.match(r"^\s*-?\d+-?\s*$", s):
        return True
    letters = [ch for ch in s if ch.isalpha()]
    if letters and sum(ch.isupper() for ch in letters) / len(letters) > 0.55:
        return True
    # starts with a long ALL-CAPS heading run (>= ~8 consecutive caps words)
    if re.match(r"^(?:[A-Z][A-Z'\u2019]*[ ,/]+){8,}", s):
        return True
    return False


def clean_factors(rep_factors, want=10):
    """Clean each candidate, drop any that are still cruft, and return up to
    `want` good sentences (so a skipped junk line is backfilled from the pool)."""
    out = []
    for f in rep_factors:
        c = clean_artifacts(f)
        if not looks_like_cruft(c):
            out.append(c)
        if len(out) >= want:
            break
    return out


# Fillers that mark a parsed "company name" as actually being boilerplate risk
# text the extractor grabbed by mistake.
_BAD_NAME_RE = re.compile(
    r"\b(risk factor|forward-looking|you should|carefully consider|the company cautions"
    r"|additional risk|any of the risks|any or all|caption|item 1a|annual report"
    r"|accumulated deficit|net loss|we derive|our revenues)\b", re.I)


def deslug(slug):
    """Best-effort readable company name from an UPPERCASE concatenated slug,
    e.g. 'ACUITYBRANDSINC' -> 'ACUITYBRANDS INC'. Imperfect for fully-glued
    multi-word names, but far better than leaking boilerplate text."""
    s = slug
    # Many bad slugs have the risk-factor text glued on after the real name,
    # e.g. 'QUIGLEYCORPITEMARISKFACTORSWEHAVE...'. Cut at the ITEM/RISKFACTOR marker.
    s = re.split(r"item\s*a?\s*risk\s*factors?|item\s*1a|riskfactors?",
                 s, flags=re.I)[0]
    # strip trailing scrape tokens
    for suf in ["CODE"]:
        if s.endswith(suf) and len(s) > len(suf) + 4:
            s = s[: -len(suf)]
    # split a trailing corporate suffix onto its own word for readability
    for suf in ["INCORPORATED", "HOLDINGS", "INTERNATIONAL", "CORPORATION",
                "COMPANIES", "COMPANY", "GROUP", "INC", "CORP", "CO", "LTD",
                "LLC", "PLC", "LP"]:
        m = re.search(suf + r"$", s)
        if m and len(s) > len(suf) + 2:
            s = s[: m.start()] + " " + suf
            break
    return re.sub(r"\s+", " ", s).strip() or slug


def clean_company(name, slug):
    name = clean_artifacts(name or "")
    # bad parse: too long, still has artifacts, or is boilerplate risk text
    if (len(name) > 44 or _BAD_NAME_RE.search(name)
            or any(t in name for t in ("dlra", "cmam", "dtta", "prca", "apstas"))
            or not name):
        return deslug(slug)
    # trailing boilerplate after a corporate suffix: keep through the suffix only
    m = re.search(r"^(.*?\b(?:INCORPORATED|HOLDINGS|INTERNATIONAL|CORPORATION|"
                  r"COMPANIES|COMPANY|GROUP|INC|CORP|CO|LTD|LLC|PLC|LP))\b", name)
    if m and len(m.group(1)) < len(name) - 2:
        # there is extra text after the suffix -> likely scraped junk; trim it
        return m.group(1).strip()
    return name


# assemble portfolio objects
PORTS = []
for c in CLUSTERS:
    cid = str(c["id"])
    n = NARR[cid]
    met = METRICS[cid]
    slug = slugify(n["name"])
    PORTS.append({
        "cid": cid,
        "slug": slug,
        "name": n["name"],
        "tagline": n.get("tagline", ""),
        "event_horizon": n.get("event_horizon", ""),
        "shared": n.get("shared_risk_factors", []),
        "hedge": n.get("hedge_thesis", ""),
        "signals": n.get("news_signals", []),
        # technique + rationale come from the DATA-DRIVEN selection (metrics.json),
        # not the LLM's first guess, so the label always matches the real chart.
        "technique": met.get("technique", ""),
        "rationale": met.get("technique_rationale", ""),
        "themes": met.get("themes", []),
        "prevalence": met.get("prevalence", []),
        "prevalence_frac": met.get("prevalence_frac", []),
        "order": met.get("order", []),
        "size": c["size"],
        "members": c["members"],
        "top_terms": c["top_terms"],
        "rep_factors": c["rep_factors"],
        "chart": CHARTS[cid]["data_uri"],
    })
PORTS.sort(key=lambda p: p["size"], reverse=True)


def family_of(p):
    hay = (p["name"] + " " + " ".join(p["top_terms"])).lower()
    for fam, kws in FAMILY_RULES:
        if any(k in hay for k in kws):
            return fam
    return "Industrials & Infrastructure"


for p in PORTS:
    p["family"] = family_of(p)

FAMILIES = []
for fam, _ in FAMILY_RULES:
    members = [p for p in PORTS if p["family"] == fam]
    if members:
        FAMILIES.append((fam, members))


# ---------------- shared shell ----------------
def nav_html(active_slug, depth):
    """depth: 0 for root pages, 1 for portfolios/ pages (for relative paths)."""
    prefix = "../" if depth else ""
    blocks = []
    for fam, members in FAMILIES:
        items = []
        for p in members:
            cls = "nav-item active" if p["slug"] == active_slug else "nav-item"
            items.append(
                f'<a class="{cls}" href="{prefix}portfolios/{p["slug"]}.html">'
                f'<span class="dot"></span>{e(p["name"])}'
                f'<span class="count">{p["size"]}</span></a>'
            )
        open_attr = " open" if any(p["slug"] == active_slug for p in members) else ""
        blocks.append(
            f'<details class="nav-group"{open_attr}>'
            f'<summary>{e(fam)}<span class="count">{len(members)}</span></summary>'
            f'<div class="nav-items">{"".join(items)}</div></details>'
        )
    home_cls = "nav-home active" if active_slug == "__home__" else "nav-home"
    return (
        f'<aside class="sidebar" id="sidebar">'
        f'<div class="sidebar-head">'
        f'<a class="brand" href="{prefix}index.html">'
        f'<img src="{prefix}assets/images/pure-play-logo.png" alt="Pure Play by Integral Mass" class="brand-logo">'
        f'</a></div>'
        f'<div class="search-wrap">'
        f'<input id="search" type="search" placeholder="Search portfolios, companies, risks…" autocomplete="off">'
        f'<div id="search-results" class="search-results"></div>'
        f'</div>'
        f'<nav class="nav">'
        f'<a class="{home_cls}" href="{prefix}index.html">Home</a>'
        f'<div class="nav-label">Portfolios · {len(PORTS)}</div>'
        f'{"".join(blocks)}'
        f'<div class="nav-label">About</div>'
        f'<a class="nav-home" href="{prefix}methodology.html">Methodology</a>'
        f'</nav></aside>'
    )


SITE_URL = "https://pure-play.riskrunners.com"
OG_IMAGE = SITE_URL + "/assets/images/og-pure-play.jpg"


def page(title, active_slug, depth, body, description="", canonical=""):
    prefix = "../" if depth else ""
    page_url = SITE_URL + "/" + canonical if canonical else SITE_URL + "/"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(page_url)}">

<!-- Open Graph / iMessage / Facebook / LinkedIn -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="Pure Play by Integral Mass">
<meta property="og:url" content="{e(page_url)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:secure_url" content="{OG_IMAGE}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Pure Play — a wiki on publicly traded companies to manage exposure">

<!-- Twitter / X -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{OG_IMAGE}">
<meta name="twitter:image:alt" content="Pure Play — a wiki on publicly traded companies to manage exposure">

<meta name="theme-color" content="#232d39">
<link rel="icon" href="{prefix}assets/images/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{prefix}assets/images/apple-touch-icon.png">
<link rel="stylesheet" href="{prefix}assets/site.css">
</head>
<body>
<button class="nav-toggle" id="navToggle" aria-label="Toggle navigation">☰</button>
{nav_html(active_slug, depth)}
<main class="content">
{body}
{footer()}
</main>
<script>window.SEARCH_PREFIX="{prefix}";</script>
<script src="{prefix}assets/app.js"></script>
</body>
</html>
"""


def footer():
    return f"""<footer class="site-footer">
<div class="footer-brand">{BRAND} · A wiki on publicly traded companies to manage exposure</div>
<div class="footer-links">
<a href="https://riskrunners.com" target="_blank" rel="noopener noreferrer">riskrunners.com</a>
<a href="https://integralmass.com" target="_blank" rel="noopener noreferrer">integralmass.com</a>
<a href="https://jeffersonrichards.com" target="_blank" rel="noopener noreferrer">jeffersonrichards.com</a>
</div>
<div class="footer-copy">© {YEAR} Integral Mass — a division of Richards Plus LLC. Risk data derived from 2019 SEC 10-K Item 1A filings (pre-pandemic baseline).</div>
</footer>"""


# ---------------- home page ----------------
def build_home():
    cards = []
    for p in PORTS:
        cards.append(f"""<a class="pcard" href="portfolios/{p['slug']}.html">
<div class="pcard-top"><span class="pcard-tech">{e(p['technique'])}</span><span class="pcard-n">{p['size']} cos.</span></div>
<h3>{e(p['name'])}</h3>
<p>{e(p['tagline'])}</p>
<div class="pcard-terms">{''.join(f'<span>{e(t)}</span>' for t in p['top_terms'][:4])}</div>
</a>""")
    total_cos = sum(p["size"] for p in PORTS)
    body = f"""
<header class="hero">
<img src="assets/images/pure-play-logo.png" alt="Pure Play by Integral Mass — a wiki on publicly traded companies to manage exposure" class="hero-logo">
<p class="hero-sub">A wiki on publicly traded companies to manage exposure.</p>
<p class="hero-lede">A <strong>pure play</strong> is a publicly traded company that carries the <em>same risk factors</em> as a private investment you already hold. Short the pure play and if the shared risk materializes — the event that sinks your private holding also sinks the public one — your hedge pays off. These {len(PORTS)} portfolios group {total_cos:,} companies from 2019 SEC filings by the risks they share, so you can find the pure-play hedge for whatever private exposure you carry.</p>
<div class="hero-stats">
<div><b>{len(PORTS)}</b><span>Risk Portfolios</span></div>
<div><b>{total_cos:,}</b><span>Companies</span></div>
<div><b>2019</b><span>Pre-Pandemic Baseline</span></div>
<div><b>ISO 31010</b><span>Methodology</span></div>
</div>
</header>
<section class="why">
<h2>Why 2019 data?</h2>
<p>These risk profiles are built from pre-COVID 10-K filings. After 2020, nearly every company added "pandemic" as a top risk factor, flattening the signal. The 2019 baseline is a cleaner picture of the structural risks that actually distinguish one business from another.</p>
</section>
<h2 class="grid-title">The {len(PORTS)} Risk Portfolios</h2>
<div class="pgrid">{''.join(cards)}</div>
"""
    out = page(f"Pure Play — Risk Portfolios of Publicly Traded Companies",
               "__home__", 0, body,
               "Pure Play groups publicly traded companies by shared risk factors into hedgeable portfolios, using ISO 31010 risk methods on 2019 SEC filings.",
               canonical="")
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)


def prevalence_table(p):
    """Real risk-theme prevalence, computed from the filings (metrics.json)."""
    order = p.get("order") or list(range(len(p.get("themes", []))))
    themes = p.get("themes", [])
    prev = p.get("prevalence", [])
    frac = p.get("prevalence_frac", [])
    if not themes or not prev:
        return ""
    rows = []
    for i in order:
        if i >= len(themes):
            continue
        pct = frac[i] if i < len(frac) else 0
        cnt = prev[i] if i < len(prev) else 0
        barw = max(2, round(pct * 100))
        rows.append(
            f"<tr><td class='rt-name'>{e(themes[i])}</td>"
            f"<td class='rt-bar'><span style='width:{barw}%'></span></td>"
            f"<td class='rt-val'>{pct:.0%} <small>({cnt}/{p['size']})</small></td></tr>"
        )
    return (
        "<table class='rt-table'><thead><tr>"
        "<th>Risk theme</th><th>Prevalence across portfolio</th><th>Companies</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


# ---------------- portfolio report page ----------------
def build_portfolio(p):
    shared = "".join(f"<li>{e(s)}</li>" for s in p["shared"])
    signals = "".join(f"<span class='signal'>{e(s)}</span>" for s in p["signals"])
    members = "".join(
        f'<a class="company" href="../archive/{e(m["slug"])}.html" target="_blank" rel="noopener noreferrer">{e(clean_company(m["company"], m["slug"]))}</a>'
        for m in p["members"]
    )
    factors = "".join(f"<li>{e(f)}</li>" for f in clean_factors(p["rep_factors"], 10))
    body = f"""
<article class="report">
<div class="report-head">
<div class="report-tech">{e(p['technique'])}</div>
<h1>{e(p['name'])}</h1>
<p class="report-tagline">{e(p['tagline'])}</p>
<div class="report-meta"><span>{p['size']} companies</span><span>Pure-play hedge portfolio</span><span>2019 baseline</span></div>
</div>

<section class="eh">
<h2>Event Horizon</h2>
<p>{e(p['event_horizon'])}</p>
</section>

<section>
<h2>Shared Risk Factors</h2>
<ul class="shared">{shared}</ul>
</section>

<section class="chart-section">
<h2>{e(p['technique'])}</h2>
<p class="muted">{e(p['rationale'])}</p>
<img class="chart" src="{p['chart']}" alt="{e(p['technique'])} analysis for {e(p['name'])}">
<p class="chart-note">Every value is measured from the {p['size']} companies' 2019 Item 1A filings: each percentage is the share of the portfolio that discloses that risk theme, and co-occurrence is how often two themes appear in the same company. No figures are simulated.</p>
{prevalence_table(p)}
</section>

<section class="hedge">
<h2>The Pure-Play Hedge</h2>
<p>{e(p['hedge'])}</p>
</section>

<section>
<h2>What to Watch in the News</h2>
<div class="signals">{signals}</div>
</section>

<section>
<h2>Representative Risk-Factor Language</h2>
<ul class="factors">{factors}</ul>
<p class="muted">Verbatim excerpts from Item 1A of the portfolio's 2019 10-K filings.</p>
</section>

<section class="members">
<h2>Companies in this Portfolio <span class="count">{p['size']}</span></h2>
<div class="company-list">{members}</div>
<p class="muted">Each links to its archived 2019 risk-factor source page.</p>
</section>
</article>
"""
    out = page(f"{p['name']} — Pure Play", p["slug"], 1, body, p["tagline"],
               canonical=f"portfolios/{p['slug']}.html")
    with open(os.path.join(PORT_DIR, f"{p['slug']}.html"), "w", encoding="utf-8") as f:
        f.write(out)


# ---------------- methodology page ----------------
def build_methodology():
    techs = sorted(set(p["technique"] for p in PORTS))
    tlist = "".join(f"<li>{e(t)}</li>" for t in techs)
    body = f"""
<article class="report">
<div class="report-head">
<div class="report-tech">How it works</div>
<h1>Methodology</h1>
<p class="report-tagline">From 311,000 risk-factor sentences to {len(PORTS)} hedgeable portfolios.</p>
</div>
<section class="eh">
<h2>The Pure-Play Thesis</h2>
<p>If a private investment and a public company share the same risk factors, the public company is a <strong>pure play</strong> on that risk. Shorting it hedges the private holding: the event that impairs one impairs the other. Pure Play finds those matches by grouping public companies according to the risks they actually disclose.</p>
</section>
<section>
<h2>The Pipeline</h2>
<ol class="pipeline">
<li><strong>Extract.</strong> Every Item 1A "Risk Factors" section from 2,301 companies' 2019 10-K filings — 311,514 individual risk statements — parsed to clean text.</li>
<li><strong>Vectorize &amp; cluster.</strong> Each company becomes a TF-IDF document over its risk language; k-means groups companies that describe the same risks into {len(PORTS)} portfolios.</li>
<li><strong>Analyze.</strong> Each portfolio is named and framed as an event horizon, with the single ISO 31010 technique that best fits its dominant uncertainty.</li>
<li><strong>Publish.</strong> Self-contained report pages with search and cross-links, deployable as a static site.</li>
</ol>
</section>
<section>
<h2>ISO 31010 Techniques Applied</h2>
<ul class="shared">{tlist}</ul>
<p class="muted">Each portfolio uses the technique matched to its risk structure: distributional risks get Monte Carlo, binary-outcome risks get Decision Trees, state-transition risks get Markov analysis, and so on.</p>
</section>
<section class="eh">
<h2>Why a 2019 Baseline</h2>
<p>Post-2020 filings are dominated by pandemic language that nearly every company added at once, which washes out the structural differences between businesses. The 2019 set is a cleaner signal of the risks that genuinely separate one company from another.</p>
</section>
</article>
"""
    out = page("Methodology — Pure Play", "__method__", 0, body,
               "How Pure Play turns 2019 SEC risk-factor filings into hedgeable risk portfolios using ISO 31010 methods.",
               canonical="methodology.html")
    with open(os.path.join(ROOT, "methodology.html"), "w", encoding="utf-8") as f:
        f.write(out)


# ---------------- search index ----------------
def build_search_index():
    idx = []
    seen_co = set()
    for p in PORTS:
        idx.append({"t": p["name"], "k": "Portfolio", "u": f"portfolios/{p['slug']}.html", "d": p["tagline"]})
        for m in p["members"]:
            co = clean_company(m["company"], m["slug"])
            key = (co, p["slug"])
            if key in seen_co:
                continue
            seen_co.add(key)
            idx.append({"t": co, "k": "Company", "u": f"portfolios/{p['slug']}.html", "d": p["name"]})
    with open(os.path.join(ASSETS, "search-index.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False)
    return len(idx)


def main():
    build_home()
    for p in PORTS:
        build_portfolio(p)
    build_methodology()
    n = build_search_index()
    print(f"built: index.html, methodology.html, {len(PORTS)} portfolio pages")
    print(f"search index entries: {n}")


if __name__ == "__main__":
    main()
