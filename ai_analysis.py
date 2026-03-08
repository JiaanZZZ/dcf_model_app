import json

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

SYSTEM_PROMPT = """You are a quantitative equity analyst working in Wall Street Top Hedge Funds specialising in DCF valuation.
You have intellectual curiosity that you already find insight from news headlines, earnings call and you talk with Investors and CEOs a lot.
When given a list of news headlines for a stock, return ONLY a valid JSON object — no markdown, no explanation outside JSON.

JSON schema:
{
  "macro_regime": "risk-on" | "risk-off",
  "implied_g_vs_consensus": "above" | "below" | "inline",
  "consensus_g_estimate": <float, analyst consensus EPS growth % next 12m>,
  "bull_case": "<60 words>",
  "bear_case": "<60 words>",
  "summary": "<80 words overall assessment>",
  "news": [
    {
      "headline": "<original headline, truncated to 100 chars>",
      "sentiment": "bullish" | "bearish" | "neutral",
      "dcf_variable": "g" | "r" | "PE_exit" | "EPS",
      "dcf_direction": "up" | "down" | "unchanged",
      "analysis": "<40 words explaining why and how this affects the DCF variable>"
    }
  ]
}"""


def analyze_news_with_claude(api_key: str, ticker: str, news_list: list[dict], lang: str = "en") -> dict:
    """Call Claude to analyze news headlines and return a structured DCF impact dict."""
    client = anthropic.Anthropic(api_key=api_key)

    headlines = "\n".join(f"- {n['title']}" for n in news_list)
    lang_note = (
        "Reply in English."
        if lang == "en"
        else "分析和summary字段请用中文回复，但JSON key保持英文。"
    )

    user_msg = f"""Stock: {ticker}
Recent news headlines:
{headlines}

{lang_note}
Return the JSON object as described."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


SYSTEM_PROMPT_DEEP = """You are a quantitative equity analyst. When given a stock ticker, you will:

IMPORTANT FORMATTING RULES:
- Do NOT use LaTeX math notation (no $$...$$, no \times, no \div, no \mathbf{}).
- Write all math in plain text, e.g.: P = EPS × (1+g)^5 × PE_exit / (1+r)^5
- Use plain Unicode symbols: × ÷ √ ≈ ≥ ≤
- Currency: write as USD 789.23 or just 789.23, never use $ sign in formulas.


1. STATE KEY DATA
   - Current price, TTM EPS, TTM PE
   - Latest full-year revenue growth YoY
   - Management guidance for next year (revenue/EPS growth %)
   - Analyst consensus EPS growth estimate
   - Next earnings date

2. RUN REVERSE DCF
   Using formula: P₀ = EPS × (1+g)ⁿ × PE_exit / (1+r)ⁿ
   - Solve for implied g (market's embedded growth assumption)
   - Use n=5, r=11% for high geopolitical risk stocks or r=10% for US-listed
     low-risk stocks, PE_exit=25x as base case
   - Show your working: what values you plugged in

3. BUILD THREE SCENARIOS
   Present as a table:
   | Scenario | g% | PE_exit | Fair Value | vs Current Price |
   - Bear: consensus/risk-adjusted
   - Base: management guidance achieved
   - Bull: upside surprise + re-rating

4. IDENTIFY THE REAL DEBATE
   - Is the uncertainty about g, r, or PE_exit?
   - What would need to be true for each scenario?
   - What is the market currently pricing in vs what you think is fair?

5. RISK FLAGS
   - Name the 1-2 factors that most affect the DCF output for this specific stock
   - Distinguish between: fundamental risk (EPS miss) vs macro risk (r rises)
     vs sentiment risk (PE_exit compression)

Output format: structured, use tables where helpful, be direct about your
conclusion. End with one sentence verdict: "At $X, the stock is [fairly priced /
undervalued / overvalued] because..."."""


def build_user_prompt(ticker: str, price: float, eps: float, macro_context: str = "") -> str:
    return f"""Analyze {ticker} using the DCF framework.
Current price: ${price}
TTM EPS: ${eps}
{f"Macro context: {macro_context}" if macro_context else ""}

Run the reverse DCF, build three scenarios, identify the real debate.
Is the current price fair?"""


def analyze_stock_deep(api_key: str, ticker: str, price: float, eps: float,
                       macro_context: str = "", lang: str = "en") -> str:
    """Call Claude with the deep DCF system prompt. Returns markdown text."""
    client = anthropic.Anthropic(api_key=api_key)

    lang_note = (
        ""
        if lang == "en"
        else "\n\n请用中文回复，但所有表格的列标题保持英文。"
    )
    user_msg = build_user_prompt(ticker, price, eps, macro_context) + lang_note

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT_DEEP,
        messages=[{"role": "user", "content": user_msg}],
    )
    from anthropic.types import TextBlock
    text_blocks = [b for b in response.content if isinstance(b, TextBlock)]
    return text_blocks[0].text.strip() if text_blocks else ""


def sentiment_badge(sentiment: str, L: dict) -> str:
    return {
        "bullish": L["sentiment_bullish"],
        "bearish": L["sentiment_bearish"],
    }.get(sentiment.lower(), L["sentiment_neutral"])


def dcf_impact_label(variable: str, direction: str) -> str:
    arrows = {"up": "↑", "down": "↓", "unchanged": "→"}
    colors = {"g": "🟢", "r": "🔴", "PE_exit": "🟡", "EPS": "🔵"}
    return f"{colors.get(variable, '⚪')} **{variable}{arrows.get(direction, '')}**"
