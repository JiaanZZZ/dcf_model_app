try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False


def fetch_stock_data(ticker: str) -> tuple[float, float, list[dict]]:
    """Return (price, ttm_eps, news_list) for the given ticker, or raise on failure."""
    t = yf.Ticker(ticker)
    info = t.info

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    ttm_eps = info.get("trailingEps")

    try:
        raw_news = t.news or []
    except Exception:
        raw_news = []

    news_list = []
    for item in raw_news[:8]:
        # yfinance >=0.2.x nests content under "content" key
        if isinstance(item, dict) and "content" in item:
            inner = item["content"]
            title = inner.get("title", "")
            link = (inner.get("canonicalUrl") or {}).get("url", "")
        else:
            title = item.get("title", "")
            link = item.get("link", "")
        if title:
            news_list.append({"title": title, "link": link})

    return float(price), float(ttm_eps), news_list
