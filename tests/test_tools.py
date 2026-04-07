from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.tools.news import fetch_news
from app.tools.price import _pct_change, fetch_price_data
from app.tools.profile import fetch_company_profile
from app.models.evidence import PriceSnapshot


def _snap(close: float, d: int = 1) -> PriceSnapshot:
    return PriceSnapshot(
        date=date(2024, 1, d), open=close, high=close, low=close, close=close, volume=1_000_000
    )


class TestPriceTool:
    @patch("app.tools.price.yf")
    def test_returns_price_data(self, mock_yf):
        import pandas as pd

        # Create mock history DataFrame
        dates = pd.date_range("2024-01-01", periods=30, freq="B")
        data = {
            "Open": [180 + i * 0.5 for i in range(30)],
            "High": [182 + i * 0.5 for i in range(30)],
            "Low": [179 + i * 0.5 for i in range(30)],
            "Close": [181 + i * 0.5 for i in range(30)],
            "Volume": [50000000 + i * 100000 for i in range(30)],
        }
        hist = pd.DataFrame(data, index=dates)

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = hist
        mock_ticker.info = {"fiftyTwoWeekHigh": 230.0, "fiftyTwoWeekLow": 160.0}
        mock_yf.Ticker.return_value = mock_ticker

        result = fetch_price_data.invoke({"ticker": "AAPL", "period": "3mo"})

        assert result is not None
        assert result["ticker"] == "AAPL"
        assert len(result["prices"]) == 30
        assert result["current_price"] > 0

    @patch("app.tools.price.yf")
    def test_returns_none_on_empty(self, mock_yf):
        import pandas as pd

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_yf.Ticker.return_value = mock_ticker

        result = fetch_price_data.invoke({"ticker": "INVALID", "period": "3mo"})
        assert result is None

    @patch("app.tools.price.yf")
    def test_handles_exception(self, mock_yf):
        mock_yf.Ticker.side_effect = Exception("Network error")
        result = fetch_price_data.invoke({"ticker": "AAPL", "period": "3mo"})
        assert result is None


class TestPctChange:
    def test_returns_none_when_not_enough_data(self):
        snaps = [_snap(100.0, i + 1) for i in range(3)]
        assert _pct_change(snaps, 5) is None

    def test_returns_none_when_past_price_is_zero(self):
        snaps = [_snap(0.0, 1), _snap(100.0, 2)]
        assert _pct_change(snaps, 1) is None

    def test_calculates_positive_change(self):
        snaps = [_snap(100.0, 1), _snap(110.0, 2)]
        assert _pct_change(snaps, 1) == 10.0

    def test_calculates_negative_change(self):
        snaps = [_snap(200.0, 1), _snap(190.0, 2)]
        assert _pct_change(snaps, 1) == -5.0

    def test_rounds_to_two_decimal_places(self):
        snaps = [_snap(300.0, 1), _snap(301.0, 2)]
        result = _pct_change(snaps, 1)
        assert result == 0.33


class TestNewsTool:
    @patch("app.tools.news.httpx.get")
    def test_returns_articles(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "headline": "Test headline",
                    "source": "Reuters",
                    "url": "https://example.com",
                    "datetime": 1706000000,
                    "summary": "Test summary",
                },
            ],
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = fetch_news.invoke({"ticker": "AAPL", "finnhub_api_key": "test-key"})

        assert len(result) == 1
        assert result[0]["headline"] == "Test headline"

    @patch("app.tools.news.httpx.get")
    def test_returns_empty_on_error(self, mock_get):
        mock_get.side_effect = Exception("API error")
        result = fetch_news.invoke({"ticker": "AAPL", "finnhub_api_key": "test-key"})
        assert result == []

    @patch("app.tools.news.httpx.get")
    def test_limits_to_15_articles(self, mock_get):
        items = [
            {
                "headline": f"Story {i}",
                "source": "Reuters",
                "url": "https://reuters.com",
                "datetime": 1706000000 + i,
                "summary": "",
            }
            for i in range(25)
        ]
        mock_get.return_value = MagicMock(status_code=200, json=lambda: items)
        mock_get.return_value.raise_for_status = MagicMock()

        result = fetch_news.invoke({"ticker": "AAPL", "finnhub_api_key": "test-key"})

        assert len(result) == 15

    @patch("app.tools.news.httpx.get")
    def test_skips_articles_with_missing_datetime(self, mock_get):
        items = [
            {"headline": "Good", "source": "Reuters", "url": "https://r.com", "datetime": 1706000000, "summary": ""},
            {"headline": "Bad", "source": "Reuters", "url": "https://r.com", "summary": ""},  # missing datetime
        ]
        mock_get.return_value = MagicMock(status_code=200, json=lambda: items)
        mock_get.return_value.raise_for_status = MagicMock()

        result = fetch_news.invoke({"ticker": "AAPL", "finnhub_api_key": "test-key"})

        assert len(result) == 1
        assert result[0]["headline"] == "Good"


class TestProfileTool:
    @patch("app.tools.profile.httpx.get")
    def test_returns_profile(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "name": "Apple Inc.",
                "ticker": "AAPL",
                "finnhubIndustry": "Technology",
                "marketCapitalization": 3000000,
                "country": "US",
                "exchange": "NASDAQ",
            },
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = fetch_company_profile.invoke({"ticker": "AAPL", "finnhub_api_key": "test-key"})

        assert result is not None
        assert result["name"] == "Apple Inc."

    @patch("app.tools.profile.httpx.get")
    def test_returns_none_on_error(self, mock_get):
        mock_get.side_effect = Exception("API error")
        result = fetch_company_profile.invoke({"ticker": "AAPL", "finnhub_api_key": "test-key"})
        assert result is None
