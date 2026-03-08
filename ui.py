import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import streamlit as st

from lang import LANG
from dcf import fair_value, implied_growth, eps_path
from data import HAS_YF, fetch_stock_data
from ai_analysis import HAS_ANTHROPIC, analyze_news_with_claude, sentiment_badge, dcf_impact_label


# ── Sidebar ───────────────────────────────────────────────────────────────

def render_sidebar(L: dict, lang_choice: str) -> dict:
    """Render sidebar controls. Returns dict of all parameter values."""
    st.sidebar.header(L["ai_section"])

    ticker_input = st.sidebar.text_input(L["ticker_input"], value="META", max_chars=8).upper().strip()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    col_btn1, col_btn2 = st.sidebar.columns(2)
    fetch_clicked = col_btn1.button(L["fetch_btn"], use_container_width=True)
    analyze_clicked = col_btn2.button(L["analyze_btn"], use_container_width=True)

    st.sidebar.divider()
    st.sidebar.header(L["params"])

    _init_session_state()
    _handle_fetch(fetch_clicked, ticker_input, L)

    if st.session_state.fetch_msg:
        if "✅" in st.session_state.fetch_msg:
            st.sidebar.success(st.session_state.fetch_msg)
        else:
            st.sidebar.error(st.session_state.fetch_msg)

    price = st.sidebar.number_input(L["price"], min_value=1.0, max_value=5000.0,
                                    value=float(st.session_state.price), step=1.0, format="%.2f")
    eps = st.sidebar.number_input(L["eps"], min_value=0.01, max_value=100.0,
                                  value=float(st.session_state.eps), step=0.1, format="%.2f")
    g = st.sidebar.slider(L["g"], 0.0, 80.0, 22.9, step=0.5)
    r = st.sidebar.slider(L["r"], 5.0, 30.0, 15.0, step=0.5)
    n = st.sidebar.slider(L["n"], 1, 10, 5, step=1)
    pe_exit = st.sidebar.slider(L["pe_exit"], 10.0, 60.0, 25.0, step=1.0)
    mode = st.sidebar.radio(L["mode"], [L["mode_reverse"], L["mode_fair"], L["mode_sense"]])

    return dict(
        ticker_input=ticker_input,
        api_key=api_key,
        fetch_clicked=fetch_clicked,
        analyze_clicked=analyze_clicked,
        price=price, eps=eps, g=g, r=r, n=n,
        pe_exit=pe_exit, mode=mode,
    )


def _init_session_state():
    defaults = {"price": 177.82, "eps": 4.90, "news_data": [], "ai_result": None, "fetch_msg": ""}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _handle_fetch(fetch_clicked: bool, ticker: str, L: dict):
    if not fetch_clicked:
        return
    if not HAS_YF:
        st.sidebar.error(L["no_yf"])
        return
    with st.sidebar, st.spinner(L["fetching"]):
        try:
            p, e, news = fetch_stock_data(ticker)
            st.session_state.price = p
            st.session_state.eps = e
            st.session_state.news_data = news
            st.session_state.fetch_msg = L["fetch_success"].format(price=p, eps=e, pe=p / e if e else 0)
        except Exception:
            st.session_state.fetch_msg = L["fetch_error"].format(ticker=ticker)


# ── AI panel ─────────────────────────────────────────────────────────────

def handle_analyze(analyze_clicked: bool, api_key: str, ticker: str, lang: str, L: dict):
    if not analyze_clicked:
        return
    if not HAS_ANTHROPIC:
        st.error(L["no_anthropic"])
    elif not api_key:
        st.error("⚠️ ANTHROPIC_API_KEY environment variable not set")
    elif not st.session_state.news_data:
        st.error("⚠️ Fetch stock data first / 请先点击拉取数据")
    else:
        with st.spinner(L["analyzing"]):
            try:
                st.session_state.ai_result = analyze_news_with_claude(
                    api_key, ticker, st.session_state.news_data, lang=lang
                )
            except Exception as ex:
                st.error(f"AI error: {ex}")


def render_ai_panel(L: dict):
    ai = st.session_state.ai_result
    if not ai:
        return

    st.subheader(L["ai_section"])

    col_macro, col_consensus, col_ig = st.columns(3)
    with col_macro:
        st.metric(L["macro_regime"],
                  "🔴 Risk-Off" if ai.get("macro_regime") == "risk-off" else "🟢 Risk-On")
    with col_consensus:
        cg = ai.get("consensus_g_estimate", "N/A")
        st.metric("Analyst Consensus g", f"{cg}%" if isinstance(cg, (int, float)) else cg)
    with col_ig:
        ig_vs = ai.get("implied_g_vs_consensus", "")
        label = {"above": "⬆ Market > Consensus", "below": "⬇ Market < Consensus",
                 "inline": "= Inline"}.get(ig_vs, ig_vs)
        st.metric(L["implied_vs_consensus"], label)

    bull_col, bear_col = st.columns(2)
    with bull_col:
        with st.container(border=True):
            st.markdown(f"**🟢 {L['bull_case']}**")
            st.caption(ai.get("bull_case", ""))
    with bear_col:
        with st.container(border=True):
            st.markdown(f"**🔴 {L['bear_case']}**")
            st.caption(ai.get("bear_case", ""))

    with st.container(border=True):
        st.markdown(f"**🤖 {L['ai_summary']}**")
        st.write(ai.get("summary", ""))

    st.markdown(f"**📰 {L['news_header']}**")
    for item in ai.get("news", []):
        badge = sentiment_badge(item.get("sentiment", "neutral"), L)
        impact = dcf_impact_label(item.get("dcf_variable", ""), item.get("dcf_direction", "unchanged"))
        with st.expander(f"{badge}  {item.get('headline', '')[:100]}"):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(item.get("analysis", ""))
            with col_b:
                st.markdown(f"**{L['impact_label']}**")
                st.markdown(impact)

    st.divider()


# ── DCF modes ─────────────────────────────────────────────────────────────

def render_eps_table(eps: float, g: float, n: int, pe_exit: float, r: float, L: dict):
    rows_raw = eps_path(eps, g, n, pe_exit, r)
    rows = []
    for row in rows_raw:
        rows.append({
            L["year"]: f"Year {row['year']}",
            L["eps_col"]: f"${row['eps']:.2f}",
            L["exit_price"]: f"${row['exit_price']:.2f}" if row["exit_price"] else "—",
            L["pv"]: f"${row['pv']:.2f}" if row["pv"] else "—",
        })
    st.table(rows)
    final = rows_raw[-1]
    st.caption(L["terminal"].format(
        n=n, fp=final["exit_price"], fe=final["eps"],
        pe=int(pe_exit), pv=final["pv"], r=r,
    ))


def render_mode_a(price: float, eps: float, g: float, r: float, n: int, pe_exit: float, L: dict):
    fv = fair_value(eps, g, n, pe_exit, r)
    ig = implied_growth(price, eps, n, pe_exit, r)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(L["implied_g"], f"{ig:.1f}%" if ig else "N/A")
    col2.metric(L["your_g"], f"{g:.1f}%")
    col3.metric(L["fair_val"], f"${fv:.2f}")
    col4.metric("TTM PE", f"{price / eps:.1f}x")
    st.divider()
    if ig:
        if ig > g:
            st.warning(L["verdict_high"].format(ig=ig, g=g))
        else:
            st.success(L["verdict_low"].format(ig=ig, g=g))
    st.subheader(L["eps_path"])
    render_eps_table(eps, g, n, pe_exit, r, L)


def render_mode_b(price: float, eps: float, g: float, r: float, n: int, pe_exit: float,
                  lang_choice: str, L: dict):
    fv = fair_value(eps, g, n, pe_exit, r)
    updown = (fv - price) / price * 100
    col1, col2, col3 = st.columns(3)
    col1.metric(L["fair_val"], f"${fv:.2f}")
    col2.metric(L["updown"], f"{updown:+.1f}%", delta_color="normal" if updown >= 0 else "inverse")
    col3.metric("TTM PE", f"{price / eps:.1f}x")
    st.divider()
    if updown > 10:
        st.success(f"{'Undervalued' if lang_choice == 'English' else '低估'} — {abs(updown):.1f}%")
    elif updown < -10:
        st.error(f"{'Overvalued' if lang_choice == 'English' else '高估'} — {abs(updown):.1f}%")
    else:
        st.info("Fair value range / 合理区间")
    st.subheader(L["eps_path"])
    render_eps_table(eps, g, n, pe_exit, r, L)


def render_mode_c(price: float, eps: float, g: float, r: float, n: int, pe_exit: float, L: dict):
    st.subheader(L["sense_title"])
    st.caption(L["sense_sub"].format(eps=eps, r=r, n=n, price=price))

    g_scenarios = [10, 15, 20, 25, 30, 40, 50]
    pe_scenarios = [15, 20, 25, 30, 35, 40]

    header = [f"{L['growth_axis']} \\ {L['pe_axis']}"] + [f"{p}x" for p in pe_scenarios]
    rows = [header]
    for gv in g_scenarios:
        row = [f"g={gv}%"]
        for pv in pe_scenarios:
            fv_cell = fair_value(eps, gv, n, pv, r)
            diff = (fv_cell - price) / price * 100
            tag = ("▲" if diff > 5 else ("▼" if diff < -5 else "─")) + f" ${fv_cell:.0f}"
            row.append(tag)
        rows.append(row)

    df = pd.DataFrame(rows[1:], columns=rows[0])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{L['legend_up']}  |  {L['legend_flat']}  |  {L['legend_down']}")
    st.divider()

    with st.expander(L["how_to"]):
        for key in ["how_1", "how_2", "how_3", "how_4", "how_5"]:
            st.markdown(L[key])


# ── Heatmap ───────────────────────────────────────────────────────────────

def render_heatmap(price: float, eps: float, g: float, r: float, n: int, pe_exit: float, L: dict):
    st.divider()
    st.subheader(L["heatmap"])

    growth_range = np.linspace(5, 50, 60)
    pe_range = np.linspace(10, 45, 60)
    G, PE = np.meshgrid(growth_range, pe_range)
    FV = fair_value(eps, G, n, PE, r)
    RETURN = (eps * (1 + G / 100) ** n * PE / price) ** (1 / n) - 1

    fig = plt.figure(figsize=(13, 4.5), facecolor="#0a0a0a")
    fig.suptitle(L["plot_title"].format(price=price, eps=eps, n=n), color="#c8f060", fontsize=11)
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.35)

    for idx, (data, title, cb_label, contour_val) in enumerate([
        (FV,           L["plot_fv"].format(r=r),  L["plot_fv_cb"],  price),
        (RETURN * 100, L["plot_ret"].format(r=r), L["plot_ret_cb"], r),
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


# ── Entry point ───────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="DCF AI Tool", layout="wide", page_icon="🤖")

    lang_choice = st.sidebar.radio("🌐 Language / 语言", ["English", "中文"])
    L = LANG["en"] if lang_choice == "English" else LANG["zh"]
    lang = "en" if lang_choice == "English" else "zh"

    st.title(L["title"])
    st.caption(L["subtitle"])
    st.divider()

    params = render_sidebar(L, lang_choice)

    handle_analyze(
        params["analyze_clicked"], params["api_key"],
        params["ticker_input"], lang, L,
    )

    render_ai_panel(L)

    p, e, g, r, n, pe = (params["price"], params["eps"], params["g"],
                          params["r"], params["n"], params["pe_exit"])

    if params["mode"] == L["mode_reverse"]:
        render_mode_a(p, e, g, r, n, pe, L)
    elif params["mode"] == L["mode_fair"]:
        render_mode_b(p, e, g, r, n, pe, lang_choice, L)
    else:
        render_mode_c(p, e, g, r, n, pe, L)

    render_heatmap(p, e, g, r, n, pe, L)
