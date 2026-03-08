# DCF Market Sensing Tool · AI Edition

A bilingual (English / 中文) interactive DCF calculator built with Streamlit, powered by Claude AI.
Reverse-engineer what the market is pricing in, stress-test your own growth assumptions, and get AI-driven news analysis — stock by stock, earnings by earnings.
<img width="1899" height="1029" alt="Screenshot 2026-03-07 at 16 53 42" src="https://github.com/user-attachments/assets/d5b25b75-39f8-42ea-bb25-78d1e99ce219" />

---

## The Formula

```
P₀ = EPS × (1 + g)ⁿ × PE_exit / (1 + r)ⁿ
```

| Variable | Meaning |
|----------|---------|
| `P₀` | Fair value today |
| `EPS` | Current trailing twelve month earnings per share |
| `g` | Annual EPS growth rate (%) |
| `n` | Forecast horizon (years) |
| `PE_exit` | Exit PE multiple at end of horizon |
| `r` | Your required annual return (%) |

---

## Features

- **Bilingual UI** — toggle between English and 中文 from the sidebar
- **Three analysis modes**
  - **Mode A — What is the market betting on?** Reverse-engineers the implied growth rate baked into the current stock price
  - **Mode B — What is the stock worth?** Computes fair value from your own assumptions and shows upside / downside vs market price
  - **Mode C — Earnings sensitivity matrix** Grid of fair values across growth rate × exit PE combinations; use this immediately after an earnings release
- **Year-by-year EPS path table** — shows how EPS compounds to the terminal value
- **Live sensitivity heatmap** — two side-by-side contour plots showing fair value and achievable annual return across the full parameter space; white line marks your target

### AI Features (NEW)

- **Auto stock data fetch** — enter a ticker and click Fetch to pull live price, TTM EPS, and latest news via yfinance
- **Claude AI news analysis** — analyzes up to 8 recent headlines and returns for each:
  - Sentiment (bullish / bearish / neutral)
  - Which DCF variable is affected (`g`, `r`, `PE_exit`, `EPS`) and direction (up / down / unchanged)
  - 40-word explanation of the impact
- **Bull & bear case summary** — Claude synthesizes the news into structured bull and bear arguments
- **Macro regime signal** — risk-on vs risk-off assessment based on current news flow
- **Implied g vs consensus** — whether the news implies growth above, below, or inline with analyst consensus

---

## Installation

```bash
pip install streamlit matplotlib numpy pandas yfinance anthropic
```

---

## Setup

The app reads your Anthropic API key from the environment. Add this to your `~/.zshrc` or `~/.bashrc`:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Then reload: `source ~/.zshrc`

---

## Usage

```bash
streamlit run dcf_streamlit_ai.py
```

Then open `http://localhost:8501` in your browser.

All parameters are controlled from the **sidebar**:

| Parameter | Default | Notes |
|-----------|---------|-------|
| Stock Price | $177.82 | NVDA as of 2026-03-07 |
| TTM EPS | $4.90 | Use non-GAAP if that's how the market prices the stock |
| Growth Rate g | 22.9% | Analyst consensus EPS growth |
| Required Return r | 15.0% | Your personal hurdle rate |
| Forecast Years n | 5 | Standard DCF horizon |
| Exit PE | 25x | Conservative assumption; adjust for sector |

---

## How to Use the AI Features

1. Enter a ticker in the sidebar (e.g. `META`, `NVDA`, `MRVL`)
2. Click **① Fetch** — auto-loads live price, EPS, and latest news
3. Click **② AI Analyze** — Claude reads the headlines and returns a structured JSON analysis
4. Review per-headline sentiment and DCF variable impact
5. Use the bull/bear summary and macro regime signal to inform your slider adjustments

---

## How to Use After Earnings

1. Find the new EPS number → update the **EPS** slider
2. Read management guidance for next quarter → convert to implied YoY growth → update **g**
3. Check Mode C sensitivity matrix — where does the fair value land vs current price?
4. If market sells off but matrix shows undervaluation → potential entry signal
5. If market rallies but matrix shows overvaluation → market may be pricing in too much

---

## Key Concepts

**TTM PE vs Exit PE**  
TTM PE is a real-time observation (`price ÷ EPS`). Exit PE is your assumption about what multiple the market will assign at the end of your forecast horizon. High-growth companies typically see PE compression as growth slows — set exit PE conservatively.

**Implied Growth Rate (Mode A)**  
Solves for `g` such that the DCF fair value equals the current market price, given your `r`, `n`, and `PE_exit`. If the implied `g` is far above analyst consensus, the stock is pricing in optimism that may not materialise.

**Why g is the most important input**  
The sensitivity heatmap makes this visible: small changes in `g` move the fair value dramatically more than equivalent changes in `PE_exit`. Always stress-test `g` against management guidance, not just analyst consensus.

**GAAP vs non-GAAP EPS**  
Use whichever EPS the market uses for valuation. For most US tech stocks this is non-GAAP (excludes stock-based compensation). Mixing GAAP EPS with a market-derived PE will produce inconsistent results.

---

## Example: NVDA vs META vs LITE vs MRVL

| Ticker | Price | TTM EPS | g | r | Exit PE | Fair Value | Signal |
|--------|-------|---------|---|---|---------|------------|--------|
| NVDA | $177.82 | $4.90 | 22.9% | 15% | 25x | ~$171 | Fair value |
| META | $645 | $23.52 | 15.3% | 15% | 22x | ~$640 | Fair value |
| LITE | $558 | $3.27 | 54% | 15% | 40x | — | Overvalued |
| MRVL | $80 | $2.85 | 31% | 15% | 25x | — | Potentially undervalued |

> These are illustrative inputs based on analyst consensus as of 2026-03-07.  
> Not investment advice. Always verify inputs against latest earnings data.

---

## File Structure

```
.
├── dcf_streamlit_ai.py   # Main Streamlit app (AI Edition)
├── dcf_streamlit.py      # Original app (no AI)
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Dependencies

```
streamlit
matplotlib
numpy
pandas
yfinance
anthropic
```

---

## Disclaimer

This tool is for educational and research purposes only.  
It is not investment advice. All inputs are assumptions — the output is only as good as the numbers you put in.  
Always cross-check growth assumptions against management guidance and latest earnings data.
