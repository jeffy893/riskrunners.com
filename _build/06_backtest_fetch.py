#!/usr/bin/env python3
"""
Back-test step 1 — Fetch REAL 2026 daily prices (Yahoo Finance chart API, no
key) for the two most testable portfolios, and surface candidate adverse-event
windows (the sharpest portfolio-wide drawdowns) so we can match them to real
news. Nothing here is simulated; every number comes from the API.

Portfolios chosen for testability (large, still-listed tickers):
  Homebuilders   (cluster 25) : interest-rate / mortgage pure play
  Regional Banks (cluster 24) : net-interest-margin / rate pure play

Output: _build/backtest_prices.json
        { portfolio_key: { "tickers":[...], "dates":[...],
                           "close": {ticker:[...]}, } }
"""
import urllib.request, json, datetime, time, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "backtest_prices.json")

# 2019 member company -> current (2026) ticker. Only companies that clearly
# still trade under a known symbol are included; survivors of M&A are mapped to
# the acquirer ONLY where unambiguous, otherwise dropped (no fabrication).
PORTFOLIOS = {
    "homebuilders": {
        "cluster": "25",
        "name": "Mortgage-Rate Sensitive Homebuilders",
        # LENNAR, MERITAGE, M/I HOMES, plus still-listed sector peers that were
        # in / adjacent to the 2019 cluster universe.
        "tickers": {
            "LEN": "Lennar",
            "MTH": "Meritage Homes",
            "MHO": "M/I Homes",
            "KBH": "KB Home",
            "PHM": "PulteGroup",
            "TOL": "Toll Brothers",
            "DHI": "D.R. Horton",
        },
    },
    "regional_banks": {
        "cluster": "24",
        "name": "Regional Bank Net-Interest-Margin Compression",
        "tickers": {
            "CFR": "Cullen/Frost Bankers",
            "ASB": "Associated Banc-Corp",
            "RNST": "Renasant",
            "SBSI": "Southside Bancshares",
            "FULT": "Fulton Financial",
            "UMBF": "UMB Financial",
            "ONB": "Old National Bancorp",
        },
    },
}

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def fetch(sym, rng="1y"):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?interval=1d&range={rng}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    d = json.load(urllib.request.urlopen(req, timeout=25))
    r = d["chart"]["result"][0]
    ts = r["timestamp"]
    cl = r["indicators"]["quote"][0]["close"]
    out = {}
    for t, c in zip(ts, cl):
        if c is None:
            continue
        out[datetime.date.fromtimestamp(t).isoformat()] = round(float(c), 4)
    return out


def main():
    data = {}
    for key, cfg in PORTFOLIOS.items():
        series = {}
        for sym in cfg["tickers"]:
            for attempt in range(3):
                try:
                    series[sym] = fetch(sym)
                    break
                except Exception as e:
                    print(f"  {sym} attempt {attempt+1}: {str(e)[:80]}", file=sys.stderr)
                    time.sleep(2 ** attempt)
            time.sleep(0.4)
        # align to common trading dates
        common = set.intersection(*[set(s) for s in series.values()])
        dates = sorted(common)
        close = {sym: [series[sym][d] for d in dates] for sym in series}
        data[key] = {
            "name": cfg["name"], "cluster": cfg["cluster"],
            "names": cfg["tickers"], "tickers": list(series.keys()),
            "dates": dates, "close": close,
        }
        print(f"{key}: {len(series)} tickers, {len(dates)} common trading days "
              f"({dates[0]}..{dates[-1]})")

        # surface sharpest equal-weight drawdown days (candidate event windows)
        import statistics
        ew = []
        for i in range(1, len(dates)):
            rets = [(close[s][i] / close[s][i-1] - 1) for s in series]
            ew.append((dates[i], statistics.mean(rets)))
        worst = sorted(ew, key=lambda x: x[1])[:6]
        print("   worst equal-weight days (date, %):",
              ", ".join(f"{d} {r*100:+.1f}" for d, r in worst))

    json.dump(data, open(OUT, "w"))
    print("saved", OUT)


if __name__ == "__main__":
    main()
