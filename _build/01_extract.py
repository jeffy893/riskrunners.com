#!/usr/bin/env python3
"""
Step 1 — Extract risk factors from every company HTML page.

Source pages live in the repo root. Each page has a table whose header cell is
    <th id='risk_factors'>Risk Factors</th>
followed by <tbody> rows, one <td> per risk-factor sentence. The first row is
the company header line ("AAON INC    Item 1A  Risk Factors"). Keyword spans are
wrapped in <font color="blue">...</font> which we strip to recover clean text.

Output: _build/risk_factors.json
    [{ "slug": "AAONINC", "file": "AAONINC.html",
       "company": "AAON INC", "factors": ["...", "..."] }, ...]
"""
import os, re, json, html, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "risk_factors.json")

SITE_PAGES = {"index.html", "about.html", "api.html", "methodology.html"}

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean(text):
    text = TAG_RE.sub("", text)          # drop <font> and any inline tags
    text = html.unescape(text)
    text = text.replace("apstas", "'s")  # artifact of the original scraper
    text = WS_RE.sub(" ", text).strip()
    return text


def extract_factors(raw):
    """Return (company_name, [factor, ...]) or (None, []) if no risk section."""
    m = re.search(r"id=['\"]risk_factors['\"]", raw)
    if not m:
        return None, []
    # Grab everything after the risk_factors header to end of that table body.
    tail = raw[m.end():]
    body = re.search(r"<tbody>(.*?)</tbody>", tail, re.S)
    if not body:
        return None, []
    rows = re.findall(r"<td>(.*?)</td>", body.group(1), re.S)
    cells = [clean(r) for r in rows]
    cells = [c for c in cells if c]
    if not cells:
        return None, []

    # First cell is the "<COMPANY>  Item 1A  Risk Factors" header line.
    header = cells[0]
    company = re.split(r"\s+Item\s*1A", header, flags=re.I)[0].strip()
    company = re.sub(r"\s{2,}", " ", company)

    factors = []
    for c in cells[1:]:
        # skip obvious section markers / page artifacts
        if re.fullmatch(r"-?\d+-?|<PAGE>|1B.*", c):
            continue
        if len(c) < 15:   # too short to be a real risk statement
            continue
        factors.append(c)
    return company, factors


def main():
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith(".html")
        and f not in SITE_PAGES
        and not f.endswith("ItemARiskFactors.html")  # duplicate variants
    )
    records = []
    skipped = 0
    for f in files:
        path = os.path.join(ROOT, f)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
        except Exception as e:
            skipped += 1
            continue
        company, factors = extract_factors(raw)
        if not factors:
            skipped += 1
            continue
        records.append({
            "slug": f[:-5],
            "file": f,
            "company": company or f[:-5],
            "factors": factors,
        })

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False)

    total_factors = sum(len(r["factors"]) for r in records)
    print(f"companies extracted: {len(records)}")
    print(f"skipped (no factors): {skipped}")
    print(f"total risk-factor sentences: {total_factors}")
    print(f"avg factors/company: {total_factors / max(1, len(records)):.1f}")
    # sample
    for r in records[:2]:
        print(f"  - {r['company']} ({r['slug']}): {len(r['factors'])} factors; "
              f"e.g. {r['factors'][0][:80]!r}")


if __name__ == "__main__":
    main()
