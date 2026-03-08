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

from ui import main

if __name__ == "__main__":
    main()
