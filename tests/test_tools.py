from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.tools.price import fetch_price_data
from app.tools.news import fetch_news
from app.tools.profile import fetch_company_profile


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
