#!/usr/bin/env python3
"""
Back-test step 2 — Honest, out-of-sample test of the pure-play hedge, using the
REAL 2026 prices fetched in step 1 and the REAL adverse events found in the news.

Method (deliberately out-of-sample so it is not circular):
  1. ESTIMATION WINDOW (a stable ~1-month stretch BEFORE the event):
       - daily log returns of every portfolio ticker
       - covariance + correlation matrices
       - minimum-variance long weights w (w>=0, sum=1) from the covariance
         matrix -- the "how much of $100 in each name" allocation the peer asked
         for, chosen on past data only.
       - average pairwise correlation = evidence the names actually co-move
         (the precondition for a pure play to work at all).
  2. EVENT WINDOW (a LATER, documented adverse event -- never overlaps estimation):
       - apply the FIXED weights as a SHORT on $100
       - P&L of the short = -1 * weighted basket return over the window
       - compare against shorting SPY (the market) over the same window, so we
         show the gain is the portfolio's shared risk firing, not just beta.

Nothing is simulated or optimized on the event window. We report whatever the
numbers say.

Events (documented in the news, see sources in the page):
  regional_banks: 2026-02-20 .. 2026-03-02  (Zions/Western Alliance borrower-
                  fraud credit losses + hot Jan PPI -> regional-bank selloff)
  homebuilders:   2026-04-28 .. 2026-05-08   (mortgage rates pushing >7%,
                  spring-selling-season demand warnings)

Output: _build/backtest_results.json
"""
import os, json, datetime
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PRICES = json.load(open(os.path.join(HERE, "backtest_prices.json")))
OUT = os.path.join(HERE, "backtest_results.json")

EVENTS = {
    "regional_banks": {
        "label": "Regional-bank credit-fraud & inflation selloff",
        "est_start": "2026-01-05", "est_end": "2026-02-13",
        "evt_start": "2026-02-20", "evt_end": "2026-03-02",
        "trigger": ("Zions Bancorporation disclosed a ~$50M charge-off and ~$60M "
                    "credit hit from borrower 'misrepresentations and contractual "
                    "defaults'; Western Alliance disclosed a fraud suit against a "
                    "borrower; a hotter-than-expected January PPI (wholesale "
                    "inflation +0.5% vs +0.3% expected) revived higher-for-longer "
                    "rate fears. Regional-bank shares fell sharply across the board."),
        "matched_risks": ["Loan portfolio credit risk / deterioration",
                           "Interest-rate & net-interest-margin sensitivity"],
        "private_analogue": ("A private investor holding an interest in a private "
                             "commercial lender or a loan fund exposed to the same "
                             "borrower-credit and rate risk would have taken a "
                             "simultaneous markdown."),
    },
    "homebuilders": {
        "label": "Mortgage-rate spike & housing-demand warning",
        "est_start": "2026-03-02", "est_end": "2026-04-10",
        "evt_start": "2026-04-28", "evt_end": "2026-05-08",
        "trigger": ("30-year mortgage rates pushed toward and past 7% into the "
                    "spring selling season; builders including Lennar and KB Home "
                    "flagged deteriorating demand, and housing data weakened. "
                    "Homebuilder shares sold off."),
        "matched_risks": ["Interest-rate / mortgage-availability sensitivity",
                          "Cyclical housing demand"],
        "private_analogue": ("A private investor in a local homebuilder, land "
                             "developer, or building-products supplier faces the "
                             "same rate-driven demand collapse."),
    },
}

SPY = None  # loaded lazily


def load_spy():
    import urllib.request
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/SPY"
           "?interval=1d&range=1y")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=25))
    r = d["chart"]["result"][0]
    out = {}
    for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
        if c:
            out[datetime.date.fromtimestamp(t).isoformat()] = float(c)
    return out


def window_idx(dates, start, end):
    return [i for i, d in enumerate(dates) if start <= d <= end]


def min_variance_weights(cov):
    """Long-only minimum-variance weights via simple projected gradient; falls
    back to inverse-variance if the solver misbehaves. Deterministic."""
    n = cov.shape[0]
    try:
        inv = np.linalg.pinv(cov)
        ones = np.ones(n)
        w = inv @ ones / (ones @ inv @ ones)
        if np.all(w >= -1e-6) and abs(w.sum() - 1) < 1e-6:
            return np.clip(w, 0, None) / np.clip(w, 0, None).sum()
    except Exception:
        pass
    iv = 1.0 / np.clip(np.diag(cov), 1e-9, None)
    return iv / iv.sum()


def analyze(key):
    P = PRICES[key]
    dates = P["dates"]
    tickers = P["tickers"]
    close = {t: np.array(P["close"][t], float) for t in tickers}
    ev = EVENTS[key]

    ei = window_idx(dates, ev["est_start"], ev["est_end"])
    vi = window_idx(dates, ev["evt_start"], ev["evt_end"])
    assert ei and vi and max(ei) < min(vi), "windows must be ordered & non-overlapping"

    # log returns over estimation window
    R = np.column_stack([np.diff(np.log(close[t][ei[0]:ei[-1] + 2])) for t in tickers])
    cov = np.cov(R, rowvar=False)
    corr = np.corrcoef(R, rowvar=False)
    w = min_variance_weights(cov)

    avg_corr = (corr.sum() - corr.shape[0]) / (corr.shape[0] ** 2 - corr.shape[0])

    # EVENT WINDOW: simple (arithmetic) returns from last est-day close to each
    # event day; short P&L on $100.
    base_i = vi[0] - 1  # day before event window starts
    def total_ret(prices):
        return prices[vi[-1]] / prices[base_i] - 1.0
    per_name = {t: total_ret(close[t]) for t in tickers}
    basket_ret = sum(w[j] * per_name[tickers[j]] for j in range(len(tickers)))
    short_pnl = -100.0 * basket_ret  # $ gain on a $100 short

    # market comparison
    global SPY
    if SPY is None:
        SPY = load_spy()
    spy = np.array([SPY.get(d, np.nan) for d in dates])
    spy_ret = spy[vi[-1]] / spy[base_i] - 1.0
    spy_short_pnl = -100.0 * spy_ret

    # daily cumulative short P&L path through the event window (for the chart)
    path_dates, path_basket, path_spy = [], [], []
    for i in vi:
        br = sum(w[j] * (close[tickers[j]][i] / close[tickers[j]][base_i] - 1) for j in range(len(tickers)))
        path_dates.append(dates[i])
        path_basket.append(-100.0 * br)
        path_spy.append(-100.0 * (spy[i] / spy[base_i] - 1))

    weights = sorted(
        [{"ticker": tickers[j], "name": P["names"][tickers[j]],
          "weight": round(float(w[j]), 4),
          "event_return": round(float(per_name[tickers[j]]), 4)}
         for j in range(len(tickers))],
        key=lambda x: -x["weight"])

    return {
        "key": key, "name": P["name"], "cluster": P["cluster"],
        "event": ev,
        "est_window": [ev["est_start"], ev["est_end"]],
        "evt_window": [ev["evt_start"], ev["evt_end"]],
        "tickers": tickers,
        "names": P["names"],
        "avg_correlation": round(float(avg_corr), 3),
        "corr": [[round(float(x), 3) for x in row] for row in corr],
        "weights": weights,
        "basket_event_return": round(float(basket_ret), 4),
        "short_pnl_per_100": round(float(short_pnl), 2),
        "spy_event_return": round(float(spy_ret), 4),
        "spy_short_pnl_per_100": round(float(spy_short_pnl), 2),
        "edge_vs_market": round(float(short_pnl - spy_short_pnl), 2),
        "path": {"dates": path_dates, "basket": [round(x, 2) for x in path_basket],
                 "spy": [round(x, 2) for x in path_spy]},
    }


def main():
    results = {}
    for key in ["regional_banks", "homebuilders"]:
        r = analyze(key)
        results[key] = r
        print(f"\n=== {r['name']} ===")
        print(f"  est {r['est_window'][0]}..{r['est_window'][1]}  "
              f"event {r['evt_window'][0]}..{r['evt_window'][1]}")
        print(f"  avg intra-portfolio correlation (est): {r['avg_correlation']}")
        print(f"  weights: " + ", ".join(f"{w['ticker']} {w['weight']:.0%}" for w in r['weights']))
        print(f"  basket event return: {r['basket_event_return']:+.1%}  "
              f"-> SHORT $100 gain = ${r['short_pnl_per_100']:+.2f}")
        print(f"  SPY event return:    {r['spy_event_return']:+.1%}  "
              f"-> SHORT $100 gain = ${r['spy_short_pnl_per_100']:+.2f}")
        print(f"  edge vs shorting the market: ${r['edge_vs_market']:+.2f}")
    json.dump(results, open(OUT, "w"))
    print("\nsaved", OUT)


if __name__ == "__main__":
    main()
