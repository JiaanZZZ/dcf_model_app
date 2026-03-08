import json

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

SYSTEM_PROMPT = """You are a quantitative equity analyst specialising in DCF valuation.
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


def sentiment_badge(sentiment: str, L: dict) -> str:
    return {
        "bullish": L["sentiment_bullish"],
        "bearish": L["sentiment_bearish"],
    }.get(sentiment.lower(), L["sentiment_neutral"])


def dcf_impact_label(variable: str, direction: str) -> str:
    arrows = {"up": "↑", "down": "↓", "unchanged": "→"}
    colors = {"g": "🟢", "r": "🔴", "PE_exit": "🟡", "EPS": "🔵"}
    return f"{colors.get(variable, '⚪')} **{variable}{arrows.get(direction, '')}**"
