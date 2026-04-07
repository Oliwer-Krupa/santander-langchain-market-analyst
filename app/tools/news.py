import logging
from datetime import datetime, timedelta

import httpx
from langchain_core.tools import tool

from app.models.evidence import NewsArticle

logger = logging.getLogger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"


@tool
def fetch_news(ticker: str, finnhub_api_key: str, days_back: int = 30) -> list[dict]:
    """Fetch recent company news articles from Finnhub for a given ticker.

    Returns up to 15 most recent articles with headline, source, URL,
    publication date, and summary.
    """
    try:
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        response = httpx.get(
            f"{FINNHUB_BASE}/company-news",
            params={
                "symbol": ticker,
                "from": from_date,
                "to": to_date,
                "token": finnhub_api_key,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            logger.warning("No news returned for %s", ticker)
            return []

        articles = []
        for item in data[:15]:
            try:
                articles.append(
                    NewsArticle(
                        headline=item.get("headline", ""),
                        source=item.get("source", "Unknown"),
                        url=item.get("url", ""),
                        published_at=datetime.fromtimestamp(item["datetime"]),
                        summary=item.get("summary", ""),
                    ).model_dump(mode="json")
                )
            except (KeyError, ValueError):
                continue

        logger.info("Fetched %d news articles for %s", len(articles), ticker)
        return articles

    except Exception:
        logger.exception("Failed to fetch news for %s", ticker)
        return []
