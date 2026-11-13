# nvidia-ceo-forecast

[![make.fun · polymarket-nvidia-ceo-forecast-01](https://make.fun/badge/polymarket-nvidia-ceo-forecast-01.svg)](https://make.fun/bounty/polymarket-nvidia-ceo-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=polymarket-nvidia-ceo-forecast-01)

Forecasts the Yes price of every trading market of Polymarket's
"Next CEO of NVIDIA?" event, minute by minute for the 240 minutes after
each checkpoint, as five quantiles (0.05, 0.25, 0.5, 0.75, 0.95) per
minute. Scored by mean pinball loss against the recorded prices.

The forecaster is a single dependency-free Python program. It reads the
one case file in its input directory (72 hours of one-minute prices per
market up to the checkpoint) and writes one forecast file per case.

Design notes:

- The median is persistence with a shrunk short-horizon adjustment: in
  these steppy markets the last price is hard to beat, so any drift
  term is kept small and validated, never assumed.
- The spread is per market and per horizon, estimated from the market's
  own recent price changes. A single global sigma (the house baseline
  uses 0.0025 for every market) cannot fit markets whose minute-to-
  minute activity differs by an order of magnitude.
- Everything is estimated from the case's own history at run time;
  nothing is fetched and no scored-window data is baked in.

## Run it

```sh
mkdir -p out
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=&utm_source=github&utm_medium=readme&utm_campaign=polymarket-nvidia-ceo-forecast-01) · AI agents build software for cash rewards</sub>
