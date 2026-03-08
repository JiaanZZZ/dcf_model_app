"""
DCF Market Sensing Tool — AI Edition
=====================================
新增功能：
  ① yfinance 自动拉取股价 / EPS
  ② Yahoo Finance 新闻推送
  ③ Claude AI 分析每条新闻对 g / r / PE_exit 的影响

安装依赖：
    pip install streamlit matplotlib numpy pandas yfinance anthropic

运行：
    streamlit run dcf_streamlit_ai.py
"""

import os
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import json

# ── 可选依赖（graceful fallback） ─────────────────────────────────────────
try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# ── 语言包 ────────────────────────────────────────────────────────────────
LANG = {
    "en": {
        "title": "DCF Market Sensing Tool · AI Edition",
        "subtitle": "P₀ = EPS × (1+g)ⁿ × PE_exit / (1+r)ⁿ",
        "lang_label": "Language",
        "params": "Parameters",
        "price": "Current Stock Price ($)",
        "eps": "Current EPS — TTM ($)",
        "g": "Expected Annual Growth Rate (g %)",
        "r": "Required Annual Return (r %)",
        "n": "Forecast Years (n)",
        "pe_exit": "Exit PE Multiple",
        "mode": "Analysis Mode",
        "mode_reverse": "A — What is the market betting on?",
        "mode_fair": "B — What is the stock worth?",
        "mode_sense": "C — Sensitivity matrix",
        "implied_g": "Market Implied Growth",
        "your_g": "Your Growth Assumption",
        "fair_val": "Fair Value",
        "premium": "Premium / Discount",
        "verdict_high": "⚠️  Market more optimistic than you ({ig:.1f}% implied vs {g:.1f}% yours). If growth only hits {g:.1f}%, stock faces downward pressure.",
        "verdict_low": "✅  Market more conservative than you ({ig:.1f}% implied vs {g:.1f}% yours). If growth hits {g:.1f}%, stock has upside.",
        "eps_path": "EPS Path — Year by Year",
        "year": "Year", "eps_col": "EPS ($)", "exit_price": "Exit Price ($)", "pv": "PV Today ($)",
        "terminal": "Year {n} exit = ${fp:.2f} (EPS ${fe:.2f} × {pe}x) → discounted = ${pv:.2f} at {r:.0f}%/yr",
        "updown": "Upside / Downside vs Market",
        "sense_title": "Fair Value Matrix — Sensitivity",
        "sense_sub": "EPS=${eps:.2f} | r={r:.1f}% | n={n}yr | Price=${price:.2f}",
        "growth_axis": "g (%/yr)", "pe_axis": "Exit PE",
        "legend_up": "▲ Undervalued (>5%)", "legend_flat": "─ Fair range", "legend_down": "▼ Overvalued (>5%)",
        "how_to": "📋 How to use after earnings",
        "how_1": "1. EPS beat/miss → adjust EPS slider",
        "how_2": "2. Read management guidance → adjust g slider",
        "how_3": "3. Matrix fair value vs actual market reaction",
        "how_4": "4. Market drops but matrix = undervalued → buy signal",
        "how_5": "5. Market rallies but matrix = overvalued → priced in too much",
        "plot_title": "DCF Sensitivity  |  ${price:.2f}  EPS ${eps:.2f}  n={n}yr",
        "plot_fv": "Fair Value\n(white = current price)",
        "plot_ret": "Annual Return\n(white = {r:.0f}% target)",
        "plot_xlabel": "Growth g (%)", "plot_ylabel": "Exit PE",
        "plot_fv_cb": "Fair Value ($)", "plot_ret_cb": "Annual Return (%)",
        "plot_assumption": "Assumption (g={g}%, PE={pe}x)",
        "heatmap": "Sensitivity Heatmap",
        # AI新增
        "ai_section": "🤖 AI News Analysis",
        "ticker_input": "Stock Ticker (e.g. META, ADI, GEV)",
        "api_key_input": "Anthropic API Key",
        "fetch_btn": "① Fetch Price & EPS",
        "analyze_btn": "② Analyze News with AI",
        "fetching": "Fetching data...",
        "analyzing": "Claude is analyzing news...",
        "no_yf": "⚠️ yfinance not installed. Run: pip install yfinance",
        "no_anthropic": "⚠️ anthropic not installed. Run: pip install anthropic",
        "no_api_key": "⚠️ Enter Anthropic API key in sidebar",
        "fetch_success": "✅ Loaded: ${price:.2f} | EPS ${eps:.2f} | TTM PE {pe:.1f}x",
        "fetch_error": "❌ Could not fetch {ticker}. Check ticker symbol.",
        "news_header": "Recent News",
        "impact_label": "DCF Impact",
        "sentiment_bullish": "🟢 Bullish",
        "sentiment_bearish": "🔴 Bearish",
        "sentiment_neutral": "⚪ Neutral",
        "bull_case": "Bull Case",
        "bear_case": "Bear Case",
        "ai_summary": "AI Summary",
        "macro_regime": "Macro Regime",
        "implied_vs_consensus": "Implied g vs Consensus",
    },
    "zh": {
        "title": "DCF 市场预判工具 · AI 版",
        "subtitle": "P₀ = EPS × (1+g)ⁿ × PE_exit / (1+r)ⁿ",
        "lang_label": "语言",
        "params": "参数设置",
        "price": "当前股价 ($)",
        "eps": "当前 EPS — TTM ($)",
        "g": "预期年增长率 (g %)",
        "r": "要求年回报率 (r %)",
        "n": "预测年数 (n)",
        "pe_exit": "退出 PE 倍数",
        "mode": "分析模式",
        "mode_reverse": "A — 市场在赌什么？",
        "mode_fair": "B — 股票值多少钱？",
        "mode_sense": "C — 敏感性矩阵",
        "implied_g": "市场隐含增长率",
        "your_g": "你的增长假设",
        "fair_val": "公允价值",
        "premium": "溢价 / 折价",
        "verdict_high": "⚠️  市场比你乐观（隐含 {ig:.1f}% vs 你的 {g:.1f}%）。如果增长只到 {g:.1f}%，股价有下行压力。",
        "verdict_low": "✅  市场比你保守（隐含 {ig:.1f}% vs 你的 {g:.1f}%）。如果增长达到 {g:.1f}%，股价有上行空间。",
        "eps_path": "逐年 EPS 路径",
        "year": "年份", "eps_col": "EPS ($)", "exit_price": "退出股价 ($)", "pv": "折现值 ($)",
        "terminal": "第 {n} 年退出 = ${fp:.2f}（EPS ${fe:.2f} × {pe}x）→ 折现回今天 = ${pv:.2f}（要求 {r:.0f}%/年）",
        "updown": "相对市价的上行/下行",
        "sense_title": "公允价值矩阵 — 敏感性分析",
        "sense_sub": "EPS=${eps:.2f} | r={r:.1f}% | n={n}年 | 当前价=${price:.2f}",
        "growth_axis": "增长率 g (%/年)", "pe_axis": "退出 PE",
        "legend_up": "▲ 低估（>5%）", "legend_flat": "─ 合理区间", "legend_down": "▼ 高估（>5%）",
        "how_to": "📋 财报后怎么用",
        "how_1": "1. 看 EPS beat/miss → 调整 EPS 滑块",
        "how_2": "2. 看管理层 guidance → 调整 g 滑块",
        "how_3": "3. 对比矩阵公允价 vs 市场实际反应",
        "how_4": "4. 市场跌但矩阵低估 → 可能买点",
        "how_5": "5. 市场涨但矩阵高估 → 已透支",
        "plot_title": "DCF 敏感性  |  ${price:.2f}  EPS ${eps:.2f}  n={n}年",
        "plot_fv": "Fair Value\n(white = current price)",
        "plot_ret": "Annual Return\n(white = {r:.0f}% target)",
        "plot_xlabel": "Growth g (%)", "plot_ylabel": "Exit PE",
        "plot_fv_cb": "Fair Value ($)", "plot_ret_cb": "Annual Return (%)",
        "plot_assumption": "当前假设 (g={g}%, PE={pe}x)",
        "heatmap": "敏感性热图",
        # AI新增
        "ai_section": "🤖 AI 新闻分析",
        "ticker_input": "股票代码（如 META、ADI、GEV）",
        "api_key_input": "Anthropic API Key",
        "fetch_btn": "① 自动拉取股价 & EPS",
        "analyze_btn": "② 用 AI 分析新闻",
        "fetching": "正在拉取数据...",
        "analyzing": "Claude 正在分析新闻...",
        "no_yf": "⚠️ 未安装 yfinance。运行：pip install yfinance",
        "no_anthropic": "⚠️ 未安装 anthropic。运行：pip install anthropic",
        "no_api_key": "⚠️ 请在侧边栏输入 Anthropic API Key",
        "fetch_success": "✅ 已加载：${price:.2f} | EPS ${eps:.2f} | TTM PE {pe:.1f}x",
        "fetch_error": "❌ 无法获取 {ticker}，请检查股票代码",
        "news_header": "最新新闻",
        "impact_label": "DCF 变量影响",
        "sentiment_bullish": "🟢 利多",
        "sentiment_bearish": "🔴 利空",
        "sentiment_neutral": "⚪ 中性",
        "bull_case": "多头逻辑",
        "bear_case": "空头逻辑",
        "ai_summary": "AI 综合判断",
        "macro_regime": "宏观环境",
        "implied_vs_consensus": "隐含 g vs Consensus",
    }
}

# ── 核心公式 ──────────────────────────────────────────────────────────────
def fair_value(eps, g, n, pe_exit, r):
    return eps * (1 + g / 100) ** n * pe_exit / (1 + r / 100) ** n

def implied_growth(price, eps, n, pe_exit, r):
    ratio = (price * (1 + r / 100) ** n) / (eps * pe_exit)
    if ratio <= 0:
        return None
    return (ratio ** (1 / n) - 1) * 100

# ── yfinance 数据拉取 ─────────────────────────────────────────────────────
def fetch_stock_data(ticker: str):
    """返回 (price, ttm_eps, news_list) 或抛出异常"""
    t = yf.Ticker(ticker)
    info = t.info

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    ttm_eps = info.get("trailingEps")

    # 新闻（最多8条）
    try:
        raw_news = t.news or []
    except Exception:
        raw_news = []

    news_list = []
    for item in raw_news[:8]:
        # yfinance ≥0.2.x nests content under "content" key
        if isinstance(item, dict) and "content" in item:
            inner = item["content"]
            title = inner.get("title", "")
            link  = (inner.get("canonicalUrl") or {}).get("url", "")
        else:
            title = item.get("title", "")
            link  = item.get("link", "")
        if title:
            news_list.append({"title": title, "link": link})

    return float(price), float(ttm_eps), news_list

# ── Claude AI 分析 ────────────────────────────────────────────────────────
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

def analyze_news_with_claude(api_key: str, ticker: str, news_list: list, lang: str = "en") -> dict:
    client = anthropic.Anthropic(api_key=api_key)

    headlines = "\n".join(f"- {n['title']}" for n in news_list)
    lang_note = "Reply in English." if lang == "en" else "分析和summary字段请用中文回复，但JSON key保持英文。"

    user_msg = f"""Stock: {ticker}
Recent news headlines:
{headlines}

{lang_note}
Return the JSON object as described."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}]
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

# ── Sentiment badge ───────────────────────────────────────────────────────
def sentiment_badge(sentiment: str, L: dict) -> str:
    return {
        "bullish": L["sentiment_bullish"],
        "bearish": L["sentiment_bearish"],
    }.get(sentiment.lower(), L["sentiment_neutral"])

def dcf_impact_label(variable: str, direction: str) -> str:
    arrows = {"up": "↑", "down": "↓", "unchanged": "→"}
    arrow = arrows.get(direction, "")
    colors = {"g": "🟢", "r": "🔴", "PE_exit": "🟡", "EPS": "🔵"}
    icon = colors.get(variable, "⚪")
    return f"{icon} **{variable}{arrow}**"

# ── Main App ──────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="DCF AI Tool", layout="wide", page_icon="🤖")

    # 语言选择
    lang_choice = st.sidebar.radio("🌐 Language / 语言", ["English", "中文"])
    L = LANG["en"] if lang_choice == "English" else LANG["zh"]

    st.title(L["title"])
    st.caption(L["subtitle"])
    st.divider()

    # ── Sidebar: AI 配置 ──────────────────────────────────────────────────
    st.sidebar.header(L["ai_section"])

    ticker_input = st.sidebar.text_input(L["ticker_input"], value="META", max_chars=8).upper().strip()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    col_btn1, col_btn2 = st.sidebar.columns(2)

    fetch_clicked   = col_btn1.button(L["fetch_btn"],   use_container_width=True)
    analyze_clicked = col_btn2.button(L["analyze_btn"], use_container_width=True)

    st.sidebar.divider()

    # ── Sidebar: DCF 参数 ─────────────────────────────────────────────────
    st.sidebar.header(L["params"])

    # 初始化 session state
    if "price"   not in st.session_state: st.session_state.price   = 177.82
    if "eps"     not in st.session_state: st.session_state.eps     = 4.90
    if "news_data" not in st.session_state: st.session_state.news_data = []
    if "ai_result"  not in st.session_state: st.session_state.ai_result  = None
    if "fetch_msg"  not in st.session_state: st.session_state.fetch_msg  = ""

    # ① 拉取按钮
    if fetch_clicked:
        if not HAS_YF:
            st.sidebar.error(L["no_yf"])
        else:
            with st.sidebar:
                with st.spinner(L["fetching"]):
                    try:
                        p, e, news = fetch_stock_data(ticker_input)
                        st.session_state.price     = p
                        st.session_state.eps       = e
                        st.session_state.news_data = news
                        st.session_state.fetch_msg = L["fetch_success"].format(
                            price=p, eps=e, pe=p/e if e else 0)
                    except Exception as ex:
                        st.session_state.fetch_msg = L["fetch_error"].format(ticker=ticker_input)

    if st.session_state.fetch_msg:
        if "✅" in st.session_state.fetch_msg:
            st.sidebar.success(st.session_state.fetch_msg)
        else:
            st.sidebar.error(st.session_state.fetch_msg)

    price   = st.sidebar.number_input(L["price"],   min_value=1.0,  max_value=5000.0, value=float(st.session_state.price), step=1.0, format="%.2f")
    eps     = st.sidebar.number_input(L["eps"],     min_value=0.01, max_value=100.0,  value=float(st.session_state.eps),   step=0.1, format="%.2f")
    g       = st.sidebar.slider(L["g"],             0.0,  80.0,  22.9, step=0.5)
    r       = st.sidebar.slider(L["r"],             5.0,  30.0,  15.0, step=0.5)
    n       = st.sidebar.slider(L["n"],             1,    10,    5,    step=1)
    pe_exit = st.sidebar.slider(L["pe_exit"],       10.0, 60.0,  25.0, step=1.0)
    mode    = st.sidebar.radio(L["mode"], [L["mode_reverse"], L["mode_fair"], L["mode_sense"]])

    # ② AI分析按钮
    if analyze_clicked:
        if not HAS_ANTHROPIC:
            st.error(L["no_anthropic"])
        elif not api_key:
            st.error("⚠️ ANTHROPIC_API_KEY environment variable not set")
        elif not st.session_state.news_data:
            st.error("⚠️ Fetch stock data first / 请先点击拉取数据")
        else:
            with st.spinner(L["analyzing"]):
                try:
                    result = analyze_news_with_claude(
                        api_key, ticker_input,
                        st.session_state.news_data,
                        lang="en" if lang_choice == "English" else "zh"
                    )
                    st.session_state.ai_result = result
                except Exception as ex:
                    st.error(f"AI error: {ex}")

    # ── 计算 ──────────────────────────────────────────────────────────────
    fv     = fair_value(eps, g, n, pe_exit, r)
    ig     = implied_growth(price, eps, n, pe_exit, r)
    ttm_pe = price / eps
    updown = (fv - price) / price * 100

    # ── AI 新闻面板（顶部展示）───────────────────────────────────────────
    ai = st.session_state.ai_result
    if ai:
        st.subheader(L["ai_section"])

        col_macro, col_regime, col_ig = st.columns(3)
        with col_macro:
            st.metric(L["macro_regime"],
                      "🔴 Risk-Off" if ai.get("macro_regime") == "risk-off" else "🟢 Risk-On")
        with col_regime:
            consensus_g = ai.get("consensus_g_estimate", "N/A")
            st.metric("Analyst Consensus g", f"{consensus_g}%" if isinstance(consensus_g, (int, float)) else consensus_g)
        with col_ig:
            ig_vs = ai.get("implied_g_vs_consensus", "")
            label = {"above": "⬆ Market > Consensus", "below": "⬇ Market < Consensus", "inline": "= Inline"}.get(ig_vs, ig_vs)
            st.metric(L["implied_vs_consensus"], label)

        # Bull / Bear
        bull_col, bear_col = st.columns(2)
        with bull_col:
            with st.container(border=True):
                st.markdown(f"**🟢 {L['bull_case']}**")
                st.caption(ai.get("bull_case", ""))
        with bear_col:
            with st.container(border=True):
                st.markdown(f"**🔴 {L['bear_case']}**")
                st.caption(ai.get("bear_case", ""))

        # Summary
        with st.container(border=True):
            st.markdown(f"**🤖 {L['ai_summary']}**")
            st.write(ai.get("summary", ""))

        # 逐条新闻
        st.markdown(f"**📰 {L['news_header']}**")
        news_analyzed = ai.get("news", [])
        for item in news_analyzed:
            sentiment = item.get("sentiment", "neutral")
            badge     = sentiment_badge(sentiment, L)
            variable  = item.get("dcf_variable", "")
            direction = item.get("dcf_direction", "unchanged")
            impact    = dcf_impact_label(variable, direction)

            with st.expander(f"{badge}  {item.get('headline', '')[:100]}"):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.write(item.get("analysis", ""))
                with col_b:
                    st.markdown(f"**{L['impact_label']}**")
                    st.markdown(impact)

        st.divider()

    # ── 模式 A: 反推隐含增长率 ────────────────────────────────────────────
    if mode == L["mode_reverse"]:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(L["implied_g"], f"{ig:.1f}%" if ig else "N/A")
        col2.metric(L["your_g"],   f"{g:.1f}%")
        col3.metric(L["fair_val"], f"${fv:.2f}")
        col4.metric("TTM PE",      f"{ttm_pe:.1f}x")
        st.divider()
        if ig:
            if ig > g:
                st.warning(L["verdict_high"].format(ig=ig, g=g))
            else:
                st.success(L["verdict_low"].format(ig=ig, g=g))

        st.subheader(L["eps_path"])
        rows, eps_t = [], eps
        for yr in range(1, n + 1):
            eps_t   *= (1 + g / 100)
            exit_p   = f"${eps_t * pe_exit:.2f}" if yr == n else "—"
            pv_val   = f"${eps_t * pe_exit / (1 + r / 100) ** yr:.2f}" if yr == n else "—"
            rows.append({L["year"]: f"Year {yr}", L["eps_col"]: f"${eps_t:.2f}",
                         L["exit_price"]: exit_p, L["pv"]: pv_val})
        st.table(rows)
        final_eps   = eps * (1 + g / 100) ** n
        final_price = final_eps * pe_exit
        pv_final    = final_price / (1 + r / 100) ** n
        st.caption(L["terminal"].format(n=n, fp=final_price, fe=final_eps, pe=int(pe_exit), pv=pv_final, r=r))

    # ── 模式 B: 公允价值 ──────────────────────────────────────────────────
    elif mode == L["mode_fair"]:
        col1, col2, col3 = st.columns(3)
        col1.metric(L["fair_val"], f"${fv:.2f}")
        col2.metric(L["updown"],   f"{updown:+.1f}%", delta_color="normal" if updown >= 0 else "inverse")
        col3.metric("TTM PE",      f"{ttm_pe:.1f}x")
        st.divider()
        if updown > 10:
            st.success(f"{'Undervalued' if lang_choice == 'English' else '低估'} — {abs(updown):.1f}%")
        elif updown < -10:
            st.error(f"{'Overvalued' if lang_choice == 'English' else '高估'} — {abs(updown):.1f}%")
        else:
            st.info("Fair value range / 合理区间")

        st.subheader(L["eps_path"])
        rows, eps_t = [], eps
        for yr in range(1, n + 1):
            eps_t   *= (1 + g / 100)
            exit_p   = f"${eps_t * pe_exit:.2f}" if yr == n else "—"
            pv_val   = f"${eps_t * pe_exit / (1 + r / 100) ** yr:.2f}" if yr == n else "—"
            rows.append({L["year"]: f"Year {yr}", L["eps_col"]: f"${eps_t:.2f}",
                         L["exit_price"]: exit_p, L["pv"]: pv_val})
        st.table(rows)
        final_eps   = eps * (1 + g / 100) ** n
        final_price = final_eps * pe_exit
        pv_final    = final_price / (1 + r / 100) ** n
        st.caption(L["terminal"].format(n=n, fp=final_price, fe=final_eps, pe=int(pe_exit), pv=pv_final, r=r))

    # ── 模式 C: 敏感性矩阵 ───────────────────────────────────────────────
    elif mode == L["mode_sense"]:
        st.subheader(L["sense_title"])
        st.caption(L["sense_sub"].format(eps=eps, r=r, n=n, price=price))

        g_scenarios  = [10, 15, 20, 25, 30, 40, 50]
        pe_scenarios = [15, 20, 25, 30, 35, 40]

        header = [f"{L['growth_axis']} \\ {L['pe_axis']}"] + [f"{p}x" for p in pe_scenarios]
        rows = [header]
        for gv in g_scenarios:
            row = [f"g={gv}%"]
            for pv in pe_scenarios:
                fv_cell = fair_value(eps, gv, n, pv, r)
                diff = (fv_cell - price) / price * 100
                tag  = ("▲" if diff > 5 else ("▼" if diff < -5 else "─")) + f" ${fv_cell:.0f}"
                row.append(tag)
            rows.append(row)

        df = pd.DataFrame(rows[1:], columns=rows[0])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{L['legend_up']}  |  {L['legend_flat']}  |  {L['legend_down']}")
        st.divider()

        with st.expander(L["how_to"]):
            for key in ["how_1","how_2","how_3","how_4","how_5"]:
                st.markdown(L[key])

    # ── 热图（所有模式） ─────────────────────────────────────────────────
    st.divider()
    st.subheader(L["heatmap"])

    growth_range = np.linspace(5, 50, 60)
    pe_range     = np.linspace(10, 45, 60)
    G, PE        = np.meshgrid(growth_range, pe_range)
    FV           = fair_value(eps, G, n, PE, r)
    RETURN       = (eps * (1 + G / 100) ** n * PE / price) ** (1 / n) - 1

    fig = plt.figure(figsize=(13, 4.5), facecolor="#0a0a0a")
    fig.suptitle(L["plot_title"].format(price=price, eps=eps, n=n), color="#c8f060", fontsize=11)
    gs  = gridspec.GridSpec(1, 2, figure=fig, wspace=0.35)

    for idx, (data, title, cb_label, contour_val, _) in enumerate([
        (FV,           L["plot_fv"].format(r=r),  L["plot_fv_cb"],  price, None),
        (RETURN * 100, L["plot_ret"].format(r=r), L["plot_ret_cb"], r,    None),
    ]):
        ax = fig.add_subplot(gs[idx])
        im = ax.contourf(G, PE, data, levels=20, cmap="RdYlGn")
        ax.contour(G, PE, data, levels=[contour_val], colors="white", linewidths=1.5)
        ax.plot(g, pe_exit, "o", color="#60c8f0", markersize=9,
                label=L["plot_assumption"].format(g=g, pe=int(pe_exit)))
        plt.colorbar(im, ax=ax, label=cb_label)
        ax.set_xlabel(L["plot_xlabel"], color="#888", fontsize=9)
        ax.set_ylabel(L["plot_ylabel"], color="#888", fontsize=9)
        ax.set_title(title, color="#e8e8e0", fontsize=9)
        ax.tick_params(colors="#888", labelsize=8)
        ax.set_facecolor("#111")
        ax.legend(fontsize=7, facecolor="#1e1e1e", labelcolor="#e8e8e0", loc="upper left")
        for spine in ax.spines.values():
            spine.set_edgecolor("#222")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


if __name__ == "__main__":
    main()
