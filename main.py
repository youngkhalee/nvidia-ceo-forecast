#!/usr/bin/env python3
"""Forecast Polymarket 'Next CEO of NVIDIA?' Yes prices, minute by minute, 4h ahead.

Entry for make.fun bounty polymarket-nvidia-ceo-forecast-01 (program/v1).
Python 3.13, standard library only, no network, deterministic.

Method (v2)
-----------
The house baseline keeps the median at the last price and widens every
market's band with one fixed spread (sigma = 0.0025 / sqrt(min)).  These
markets do not share one spread: in the practice history the share of
minutes that move at all runs from ~3% to ~51% across markets, and each
market's typical tick size differs by more than an order of magnitude.
So this entry keeps the persistence median but estimates each market's
own one-minute spread from its recent one-minute changes:

  sigma_m = mean(|diff|) over the last LOOKBACK minutes / 0.7979

(mean absolute change of a Gaussian step is sigma * sqrt(2/pi); the
mean-absolute estimator is far less jump-sensitive than a root mean
square, which matters here because single-minute jumps of 0.1-0.4 do
occur).  The estimate is floored and capped so a dead market still gets
a small honest band and a chaotic one cannot explode the output.

Quantiles are Gaussian around the last price:
  q_tau(h) = clamp(x + z_tau * sigma_m * sqrt(h), 0, 1)
rounded to 6 decimals and forced non-decreasing.

Validation (practice futures p00-p04 reconstructed from the following
cases' histories; pinball loss, lower is better; the house baseline
scores 0.3925 on this same subset and 0.363589 on the full practice):
  lookback 720 (v1)  0.3329   lookback 240 (v2)  0.3195
  lookback 1440       0.3534   lookback 4320     0.3856
  lookback 360        0.3196   lookback 180      0.3217
The loss falls monotonically as the window shortens from 4320 to 240
and is flat between 240 and 360, so v2 takes 240: these markets change
regime fast and a long window carries stale volatility.  Two ideas
tested and rejected on the same check: widening the 5%/95% tails
(+0.007 loss) and a shrunk 60-minute drift term (+0.049 loss, median
error up).  The median stays pure persistence.
"""

import json
import math
import os
import sys

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.644854, -0.67449, 0.0, 0.67449, 1.644854]

LOOKBACK = 240          # minutes of recent changes used for the spread (v2: validated, see docstring)
SIGMA_FLOOR = 0.0004    # a silent market still moves sometimes
SIGMA_CAP = 0.02        # per sqrt(minute); far above any sane estimate
SQRT_2_OVER_PI = 0.7978845608028654


def price6(x):
    """Clamp to [0, 1] and round to 6 decimals (never -0.0)."""
    if x < 0.0:
        x = 0.0
    elif x > 1.0:
        x = 1.0
    return round(x, 6) + 0.0


def market_sigma(prices):
    """Per-market one-minute spread from recent absolute changes."""
    n = len(prices)
    if n < 2:
        return SIGMA_FLOOR
    start = max(1, n - LOOKBACK)
    total = 0.0
    count = 0
    prev = prices[start - 1]
    for i in range(start, n):
        d = prices[i] - prev
        prev = prices[i]
        total += d if d >= 0.0 else -d
        count += 1
    if count == 0:
        return SIGMA_FLOOR
    sigma = (total / count) / SQRT_2_OVER_PI
    if sigma < SIGMA_FLOOR:
        return SIGMA_FLOOR
    if sigma > SIGMA_CAP:
        return SIGMA_CAP
    return sigma


def forecast_market(prices, horizon):
    """240 rows of 5 quantiles for one market (persistence median)."""
    x = prices[-1]
    sigma = market_sigma(prices)
    rows = []
    for h in range(1, horizon + 1):
        w = sigma * math.sqrt(h)
        row = [price6(x + z * w) for z in Z]
        # rounding can only preserve order here, but enforce it anyway
        for j in range(1, 5):
            if row[j] < row[j - 1]:
                row[j] = row[j - 1]
        rows.append(row)
    return rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    names = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
    for name in names:
        case_id = name[:-3]
        with open(os.path.join(INPUT_DIR, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        if list(case["quantiles"]) != QUANTILES:
            raise ValueError(f"{name} asks for quantiles {case['quantiles']}")
        horizon = int(case["horizon_minutes"])
        forecasts = []
        for m in case["markets"]:
            prices = m["prices"]
            if not prices:
                raise ValueError(f"market {m['id']} has no prices")
            forecasts.append({"id": m["id"], "q": forecast_market(prices, horizon)})
        out_path = os.path.join(OUTPUT_DIR, case_id + ".out")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"forecasts": forecasts}, separators=(",", ":")))
            fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
