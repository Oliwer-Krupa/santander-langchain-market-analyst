"""Tests for SEC EDGAR filings tool."""
from datetime import date
from unittest.mock import MagicMock, call, patch

import pytest

from app.tools.filings import _get_cik, fetch_recent_filings

_TICKERS_JSON = {
    "0": {"ticker": "AAPL", "cik_str": 320193, "title": "Apple Inc."},
    "1": {"ticker": "MSFT", "cik_str": 789019, "title": "Microsoft Corp."},
}

_SUBMISSIONS = {
    "filings": {
        "recent": {
            "form": ["10-K", "10-Q", "8-K"],
            "filingDate": ["2024-11-01", "2024-08-01", "2024-07-15"],
            "primaryDocDescription": ["Annual Report", "Quarterly Report", "Current Report"],
            "accessionNumber": [
                "0000320193-24-000123",
                "0000320193-24-000456",
                "0000320193-24-000789",
            ],
        }
    }
}


class TestGetCik:
    @patch("app.tools.filings.httpx.get")
    def test_returns_zero_padded_cik_for_known_ticker(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: _TICKERS_JSON)
        mock_get.return_value.raise_for_status = MagicMock()

        result = _get_cik("AAPL")

        assert result == "0000320193"

    @patch("app.tools.filings.httpx.get")
    def test_lookup_is_case_insensitive(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: _TICKERS_JSON)
        mock_get.return_value.raise_for_status = MagicMock()

        result = _get_cik("aapl")

        assert result == "0000320193"

    @patch("app.tools.filings.httpx.get")
    def test_returns_none_when_ticker_not_in_registry(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: _TICKERS_JSON)
        mock_get.return_value.raise_for_status = MagicMock()

        result = _get_cik("ZZZZ")

        assert result is None

    @patch("app.tools.filings.httpx.get")
    def test_returns_none_on_network_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        result = _get_cik("AAPL")

        assert result is None

    @patch("app.tools.filings.httpx.get")
    def test_makes_exactly_one_http_request(self, mock_get):
        """_get_cik should only call tickers.json — the unused browse-edgar
        call was dead code that has been removed."""
        mock_get.return_value = MagicMock(json=lambda: _TICKERS_JSON)
        mock_get.return_value.raise_for_status = MagicMock()

        _get_cik("AAPL")

        assert mock_get.call_count == 1
        assert "company_tickers.json" in mock_get.call_args[0][0]


class TestFetchRecentFilings:
    @patch("app.tools.filings._get_cik", return_value="0000320193")
    @patch("app.tools.filings.httpx.get")
    def test_returns_filings_for_valid_ticker(self, mock_get, _mock_cik):
        mock_get.return_value = MagicMock(json=lambda: _SUBMISSIONS)
        mock_get.return_value.raise_for_status = MagicMock()

        result = fetch_recent_filings.invoke({"ticker": "AAPL"})

        assert len(result) == 3
        assert result[0]["form_type"] == "10-K"
        assert result[0]["filed_date"] == "2024-11-01"
        assert result[0]["description"] == "Annual Report"

    @patch("app.tools.filings._get_cik", return_value="0000320193")
    @patch("app.tools.filings.httpx.get")
    def test_filing_url_is_well_formed(self, mock_get, _mock_cik):
        mock_get.return_value = MagicMock(json=lambda: _SUBMISSIONS)
        mock_get.return_value.raise_for_status = MagicMock()

        result = fetch_recent_filings.invoke({"ticker": "AAPL"})

        assert result[0]["url"].startswith("https://www.sec.gov/Archives/edgar/data/")
        assert "0000320193-24-000123" in result[0]["url"]

    @patch("app.tools.filings._get_cik", return_value=None)
    def test_returns_empty_when_cik_not_resolved(self, _mock_cik):
        result = fetch_recent_filings.invoke({"ticker": "UNKNOWN"})

        assert result == []

    @patch("app.tools.filings._get_cik", return_value="0000320193")
    @patch("app.tools.filings.httpx.get")
    def test_returns_empty_on_network_error(self, mock_get, _mock_cik):
        mock_get.side_effect = Exception("SEC is down")

        result = fetch_recent_filings.invoke({"ticker": "AAPL"})

        assert result == []

    @patch("app.tools.filings._get_cik", return_value="0000320193")
    @patch("app.tools.filings.httpx.get")
    def test_respects_max_filings_parameter(self, mock_get, _mock_cik):
        large_submissions = {
            "filings": {
                "recent": {
                    "form": ["10-K"] * 20,
                    "filingDate": [f"2024-{i+1:02d}-01" for i in range(20)],
                    "primaryDocDescription": ["Report"] * 20,
                    "accessionNumber": [f"0000320193-24-{i:06d}" for i in range(20)],
                }
            }
        }
        mock_get.return_value = MagicMock(json=lambda: large_submissions)
        mock_get.return_value.raise_for_status = MagicMock()

        result = fetch_recent_filings.invoke({"ticker": "AAPL", "max_filings": 4})

        assert len(result) == 4

    @patch("app.tools.filings._get_cik", return_value="0000320193")
    @patch("app.tools.filings.httpx.get")
    def test_handles_missing_description_gracefully(self, mock_get, _mock_cik):
        """When primaryDocDescription is shorter than forms list, use form type."""
        sparse = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q"],
                    "filingDate": ["2024-11-01", "2024-08-01"],
                    "primaryDocDescription": [],  # empty — no descriptions
                    "accessionNumber": ["0000320193-24-000123", "0000320193-24-000456"],
                }
            }
        }
        mock_get.return_value = MagicMock(json=lambda: sparse)
        mock_get.return_value.raise_for_status = MagicMock()

        result = fetch_recent_filings.invoke({"ticker": "AAPL"})

        assert len(result) == 2
        assert result[0]["description"] == "10-K"  # falls back to form_type
