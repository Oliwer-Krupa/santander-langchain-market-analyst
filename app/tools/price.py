import logging
from datetime import date

import yfinance as yf
from langchain_core.tools import tool

from app.models.evidence import PriceData, PriceSnapshot

logger = logging.getLogger(__name__)


def _pct_change(prices: list[PriceSnapshot], days: int) -> float | None:
    """Calculate percentage change over the last N trading days."""
    if len(prices) < days + 1:
        return None
    recent = prices[-1].close
    past = prices[-(days + 1)].close
    if past == 0:
        return None
    return round(((recent - past) / past) * 100, 2)


@tool
def fetch_price_data(ticker: str, period: str = "3mo") -> dict | None:
    """Fetch historical OHLCV price data for a stock ticker using Yahoo Finance.

    Returns price snapshots, current price, and percentage changes over
    various timeframes (1 day, 5 days, 1 month).
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            logger.warning("No price data returned for %s", ticker)
            return None

        snapshots = [
            PriceSnapshot(
                date=idx.date(),
                open=round(row["Open"], 2),
                high=round(row["High"], 2),
                low=round(row["Low"], 2),
                close=round(row["Close"], 2),
                volume=int(row["Volume"]),
            )
            for idx, row in hist.iterrows()
        ]

        # 52-week high/low from info (best-effort)
        info = stock.info or {}
        high_52w = info.get("fiftyTwoWeekHigh")
        low_52w = info.get("fiftyTwoWeekLow")

        # For 1mo change, use all available data if we have fewer than 22 snapshots
        change_1mo = _pct_change(snapshots, 21)
        if change_1mo is None and len(snapshots) >= 15:
            change_1mo = _pct_change(snapshots, len(snapshots) - 1)

        price_data = PriceData(
            ticker=ticker,
            prices=snapshots,
            current_price=snapshots[-1].close,
            change_pct_1d=_pct_change(snapshots, 1),
            change_pct_5d=_pct_change(snapshots, 5),
            change_pct_1mo=change_1mo,
            high_52w=high_52w,
            low_52w=low_52w,
        )

        logger.info("Fetched %d price snapshots for %s", len(snapshots), ticker)
        return price_data.model_dump()

    except Exception:
        logger.exception("Failed to fetch price data for %s", ticker)
        return None
