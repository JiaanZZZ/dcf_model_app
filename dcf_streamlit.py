"""
DCF Market Sensing Tool — Streamlit App
========================================
安装依赖：
    pip install streamlit matplotlib numpy

运行：
    streamlit run dcf_streamlit.py
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── 语言包 ───────────────────────────────────────────────────────────────
LANG = {
    "en": {
        "title": "DCF Market Sensing Tool",
        "subtitle": "P₀ = EPS × (1+g)ⁿ × PE_exit / (1+r)ⁿ",
        "lang_label": "Language",
        "params": "Parameters",
        "price": "Current Stock Price ($)",
        "eps": "Current EPS — TTM ($)",
        "g": "Expected Annual Growth Rate (g %)",
        "r": "Your Required Annual Return (r %)",
        "n": "Forecast Years (n)",
        "pe_exit": "Exit PE Multiple",
        "mode": "Analysis Mode",
        "mode_reverse": "A — What is the market betting on?",
        "mode_fair": "B — What is the stock worth?",
        "mode_sense": "C — Earnings sensitivity matrix",
        "implied_g": "Market Implied Growth Rate",
        "your_g": "Your Growth Assumption (consensus)",
        "fair_val": "Fair Value (based on your assumptions)",
        "premium": "Premium / Discount to Market",
        "verdict_high": "⚠️  Market is more optimistic than consensus ({ig:.1f}% implied vs {g:.1f}% consensus). If growth only hits {g:.1f}%, stock faces downward pressure.",
        "verdict_low": "✅  Market is more conservative than consensus ({ig:.1f}% implied vs {g:.1f}% consensus). If growth hits {g:.1f}%, stock has upside.",
        "eps_path": "EPS Path — Year by Year",
        "year": "Year",
        "eps_col": "EPS ($)",
        "exit_price": "Exit Price ($)",
        "pv": "PV Today ($)",
        "terminal": "Year {n} exit price = ${fp:.2f} (EPS ${fe:.2f} × {pe}x) → discounted to today = ${pv:.2f} (requiring {r:.0f}%/yr)",
        "updown": "Upside / Downside vs Market",
        "sense_title": "Fair Value Matrix — Sensitivity Analysis",
        "sense_sub": "EPS=${eps:.2f} | r={r:.1f}% | n={n}yr | Current Price=${price:.2f}",
        "growth_axis": "Growth Rate g (%/yr)",
        "pe_axis": "Exit PE",
        "legend_up": "▲ = Undervalued (>5% above market)",
        "legend_flat": "─ = Fair range",
        "legend_down": "▼ = Overvalued (>5% below market)",
        "how_to": "📋 How to use after earnings",
        "how_1": "1. Check EPS beat/miss → adjust **EPS** slider",
        "how_2": "2. Read management guidance → adjust **g** slider",
        "how_3": "3. Compare matrix fair value vs actual market reaction",
        "how_4": "4. Market drops but matrix shows undervalued → possible buy signal",
        "how_5": "5. Market rallies but matrix shows overvalued → market is pricing in too much",
        "plot_title": "DCF Sensitivity  |  Price ${price:.2f}  EPS ${eps:.2f}  n={n}yr",
        "plot_fv": "Fair Value Matrix\n(white line = current price)",
        "plot_ret": "Annual Return Matrix\n(white line = your target {r:.0f}%)",
        "plot_xlabel": "Growth Rate g (%)",
        "plot_ylabel": "Exit PE",
        "plot_fv_cb": "Fair Value ($)",
        "plot_ret_cb": "Annual Return (%)",
        "plot_assumption": "Current assumption (g={g}%, PE={pe}x)",
        "heatmap": "Sensitivity Heatmap",
    },
    "zh": {
        "title": "DCF 市场预判工具",
        "subtitle": "P₀ = EPS × (1+g)ⁿ × PE_exit / (1+r)ⁿ",
        "lang_label": "语言",
        "params": "参数设置",
        "price": "当前股价 ($)",
        "eps": "当前 EPS — TTM ($)",
        "g": "预期年增长率 (g %)",
        "r": "你要求的年回报率 (r %)",
        "n": "预测年数 (n)",
        "pe_exit": "退出 PE 倍数",
        "mode": "分析模式",
        "mode_reverse": "A — 市场在赌什么？",
        "mode_fair": "B — 股票值多少钱？",
        "mode_sense": "C — 财报敏感性矩阵",
        "implied_g": "市场隐含年增长率",
        "your_g": "你的增长假设 (analyst consensus)",
        "fair_val": "公允价值（基于你的假设）",
        "premium": "溢价 / 折价",
        "verdict_high": "⚠️  市场比 analyst 更乐观（隐含 {ig:.1f}% vs consensus {g:.1f}%）。如果增长只达到 {g:.1f}%，股价有下行压力。",
        "verdict_low": "✅  市场比 analyst 保守（隐含 {ig:.1f}% vs consensus {g:.1f}%）。如果增长达到 {g:.1f}%，股价有上行空间。",
        "eps_path": "逐年 EPS 路径",
        "year": "年份",
        "eps_col": "EPS ($)",
        "exit_price": "退出股价 ($)",
        "pv": "折现值 ($)",
        "terminal": "第 {n} 年退出股价 = ${fp:.2f}（EPS ${fe:.2f} × {pe}x）→ 折现回今天 = ${pv:.2f}（要求 {r:.0f}%/年）",
        "updown": "相对市场价的上行/下行空间",
        "sense_title": "公允价值矩阵 — 敏感性分析",
        "sense_sub": "EPS=${eps:.2f} | r={r:.1f}% | n={n}年 | 当前价=${price:.2f}",
        "growth_axis": "增长率 g (%/年)",
        "pe_axis": "退出 PE",
        "legend_up": "▲ = 低估（高于市价5%以上）",
        "legend_flat": "─ = 合理区间",
        "legend_down": "▼ = 高估（低于市价5%以上）",
        "how_to": "📋 财报后怎么用这个工具",
        "how_1": "1. 看 EPS beat/miss 了多少 → 调整 **EPS** 滑块",
        "how_2": "2. 看管理层 guidance → 调整 **g** 滑块",
        "how_3": "3. 对比矩阵里的公允价 vs 市场实际反应",
        "how_4": "4. 如果市场跌但矩阵显示低估 → 可能是买点",
        "how_5": "5. 如果市场涨但矩阵显示高估 → 市场在透支未来",
        "plot_title": "DCF 敏感性分析  |  价格 ${price:.2f}  EPS ${eps:.2f}  n={n}年",
        "plot_fv": "Fair Value Matrix\n(white line = current price)",
        "plot_ret": "Annual Return Matrix\n(white line = target {r:.0f}%)",
        "plot_xlabel": "Growth Rate g (%)",
        "plot_ylabel": "Exit PE",
        "plot_fv_cb": "Fair Value ($)",
        "plot_ret_cb": "Annual Return (%)",
        "plot_assumption": "Current (g={g}%, PE={pe}x)",
        "heatmap": "敏感性热图",
    }
}

# ── 核心公式 ─────────────────────────────────────────────────────────────
def fair_value(eps, g, n, pe_exit, r):
    return eps * (1 + g/100)**n * pe_exit / (1 + r/100)**n

def implied_growth(price, eps, n, pe_exit, r):
    ratio = (price * (1 + r/100)**n) / (eps * pe_exit)
    if ratio <= 0:
        return None
    return (ratio ** (1/n) - 1) * 100

# ── Streamlit App ────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="DCF Tool", layout="wide", page_icon="📊")

    # 语言选择
    lang_choice = st.sidebar.radio("🌐 Language / 语言", ["English", "中文"])
    L = LANG["en"] if lang_choice == "English" else LANG["zh"]

    # 标题
    st.title(L["title"])
    st.caption(L["subtitle"])
    st.divider()

    # ── 侧边栏参数 ──────────────────────────────────────────────────────
    st.sidebar.header(L["params"])

    price   = st.sidebar.number_input(L["price"],   min_value=1.0,  max_value=2000.0, value=177.82, step=1.0, format="%.2f")
    eps     = st.sidebar.number_input(L["eps"],     min_value=0.1,  max_value=50.0,   value=4.90,   step=0.1, format="%.2f")
    g       = st.sidebar.number_input(L["g"],       min_value=0.0,  max_value=80.0,   value=22.9,   step=0.5, format="%.1f")
    r       = st.sidebar.number_input(L["r"],       min_value=5.0,  max_value=30.0,   value=15.0,   step=0.5, format="%.1f")
    n       = st.sidebar.number_input(L["n"],       min_value=1,    max_value=10,     value=5,      step=1)
    pe_exit = st.sidebar.number_input(L["pe_exit"], min_value=10.0, max_value=60.0,   value=25.0,   step=1.0, format="%.1f")

    mode = st.sidebar.radio(L["mode"], [L["mode_reverse"], L["mode_fair"], L["mode_sense"]])

    # ── 计算 ────────────────────────────────────────────────────────────
    fv = fair_value(eps, g, n, pe_exit, r)
    ig = implied_growth(price, eps, n, pe_exit, r)
    ttm_pe = price / eps
    updown = (fv - price) / price * 100

    # ── 模式 A：反推隐含增长率 ──────────────────────────────────────────
    if mode == L["mode_reverse"]:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(L["implied_g"], f"{ig:.1f}%" if ig else "N/A")
        col2.metric(L["your_g"], f"{g:.1f}%")
        col3.metric(L["fair_val"], f"${fv:.2f}")
        col4.metric("TTM PE", f"{ttm_pe:.1f}x")

        st.divider()

        if ig:
            if ig > g:
                st.warning(L["verdict_high"].format(ig=ig, g=g))
            else:
                st.success(L["verdict_low"].format(ig=ig, g=g))

        # EPS路径表
        st.subheader(L["eps_path"])
        rows = []
        eps_t = eps
        for yr in range(1, n+1):
            eps_t *= (1 + g/100)
            exit_p = f"${eps_t * pe_exit:.2f}" if yr == n else "—"
            pv_val = f"${eps_t * pe_exit / (1 + r/100)**yr:.2f}" if yr == n else "—"
            rows.append({
                L["year"]: f"Year {yr}",
                L["eps_col"]: f"${eps_t:.2f}",
                L["exit_price"]: exit_p,
                L["pv"]: pv_val,
            })
        st.table(rows)

        final_eps = eps * (1 + g/100)**n
        final_price = final_eps * pe_exit
        pv_final = final_price / (1 + r/100)**n
        st.caption(L["terminal"].format(n=n, fp=final_price, fe=final_eps, pe=int(pe_exit), pv=pv_final, r=r))

    # ── 模式 B：公允价值 ────────────────────────────────────────────────
    elif mode == L["mode_fair"]:
        col1, col2, col3 = st.columns(3)
        col1.metric(L["fair_val"], f"${fv:.2f}")
        col2.metric(L["updown"], f"{updown:+.1f}%",
                    delta_color="normal" if updown >= 0 else "inverse")
        col3.metric("TTM PE", f"{ttm_pe:.1f}x")

        st.divider()

        if updown > 10:
            st.success(f"{'Undervalued' if lang_choice == 'English' else '低估'} — {abs(updown):.1f}%")
        elif updown < -10:
            st.error(f"{'Overvalued' if lang_choice == 'English' else '高估'} — {abs(updown):.1f}%")
        else:
            st.info(f"{'Fair value range' if lang_choice == 'English' else '合理区间'}")

        # EPS路径表
        st.subheader(L["eps_path"])
        rows = []
        eps_t = eps
        for yr in range(1, n+1):
            eps_t *= (1 + g/100)
            exit_p = f"${eps_t * pe_exit:.2f}" if yr == n else "—"
            pv_val = f"${eps_t * pe_exit / (1 + r/100)**yr:.2f}" if yr == n else "—"
            rows.append({
                L["year"]: f"Year {yr}",
                L["eps_col"]: f"${eps_t:.2f}",
                L["exit_price"]: exit_p,
                L["pv"]: pv_val,
            })
        st.table(rows)

        final_eps = eps * (1 + g/100)**n
        final_price = final_eps * pe_exit
        pv_final = final_price / (1 + r/100)**n
        st.caption(L["terminal"].format(n=n, fp=final_price, fe=final_eps, pe=int(pe_exit), pv=pv_final, r=r))

    # ── 模式 C：敏感性矩阵 ──────────────────────────────────────────────
    elif mode == L["mode_sense"]:
        st.subheader(L["sense_title"])
        st.caption(L["sense_sub"].format(eps=eps, r=r, n=n, price=price))

        growth_scenarios = [10, 15, 20, 25, 30, 40, 50]
        pe_scenarios = [15, 20, 25, 30, 35, 40]

        # 构建矩阵数据
        header = [L["growth_axis"] + " \\ " + L["pe_axis"]] + [f"{p}x" for p in pe_scenarios]
        rows = [header]
        for gv in growth_scenarios:
            row = [f"g={gv}%"]
            for pv in pe_scenarios:
                fv_cell = fair_value(eps, gv, n, pv, r)
                diff = (fv_cell - price) / price * 100
                if diff > 5:
                    marker = "▲"
                    tag = f"▲ ${fv_cell:.0f}"
                elif diff < -5:
                    marker = "▼"
                    tag = f"▼ ${fv_cell:.0f}"
                else:
                    tag = f"─ ${fv_cell:.0f}"
                row.append(tag)
            rows.append(row)

        # 用st.dataframe显示
        import pandas as pd
        df = pd.DataFrame(rows[1:], columns=rows[0])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.caption(f"{L['legend_up']}  |  {L['legend_flat']}  |  {L['legend_down']}")
        st.divider()

        with st.expander(L["how_to"]):
            st.markdown(L["how_1"])
            st.markdown(L["how_2"])
            st.markdown(L["how_3"])
            st.markdown(L["how_4"])
            st.markdown(L["how_5"])

    # ── 热图（所有模式都显示）──────────────────────────────────────────
    st.divider()
    st.subheader(L["heatmap"])

    growth_range = np.linspace(5, 50, 60)
    pe_range     = np.linspace(10, 45, 60)
    G, PE        = np.meshgrid(growth_range, pe_range)
    FV           = fair_value(eps, G, n, PE, r)
    RETURN       = (eps * (1 + G/100)**n * PE / price) ** (1/n) - 1

    fig = plt.figure(figsize=(13, 4.5), facecolor='#0a0a0a')
    fig.suptitle(L["plot_title"].format(price=price, eps=eps, n=n),
                 color='#c8f060', fontsize=11)
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.35)

    for idx, (data, title, cb_label, contour_val, cb_fmt) in enumerate([
        (FV,           L["plot_fv"].format(r=r),  L["plot_fv_cb"],  price,  "${x:.0f}"),
        (RETURN * 100, L["plot_ret"].format(r=r), L["plot_ret_cb"], r,      "{x:.0f}%"),
    ]):
        ax = fig.add_subplot(gs[idx])
        im = ax.contourf(G, PE, data, levels=20, cmap='RdYlGn')
        ax.contour(G, PE, data, levels=[contour_val], colors='white', linewidths=1.5)
        ax.plot(g, pe_exit, 'o', color='#60c8f0', markersize=9,
                label=L["plot_assumption"].format(g=g, pe=int(pe_exit)))
        plt.colorbar(im, ax=ax, label=cb_label)
        ax.set_xlabel(L["plot_xlabel"], color='#888', fontsize=9)
        ax.set_ylabel(L["plot_ylabel"], color='#888', fontsize=9)
        ax.set_title(title, color='#e8e8e0', fontsize=9)
        ax.tick_params(colors='#888', labelsize=8)
        ax.set_facecolor('#111')
        ax.legend(fontsize=7, facecolor='#1e1e1e', labelcolor='#e8e8e0',
                  loc='upper left')
        for spine in ax.spines.values():
            spine.set_edgecolor('#222')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


if __name__ == "__main__":
    main()
