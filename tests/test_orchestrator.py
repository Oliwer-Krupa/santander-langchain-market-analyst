"""Tests for orchestrator format helpers and gather_evidence pipeline."""
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.evidence import (
    CompanyProfile,
    EvidenceBundle,
    FilingRef,
    NewsArticle,
    PriceData,
    PriceSnapshot,
)
from app.models.request import AnalysisRequest
from app.orchestrator import (
    _format_filings,
    _format_news,
    _format_price_data,
    _format_profile,
    gather_evidence,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SNAPSHOT = PriceSnapshot(
    date=date(2024, 11, 1),
    open=220.0,
    high=225.0,
    low=219.0,
    close=223.0,
    volume=55_000_000,
)

_PRICE_DATA = PriceData(
    ticker="AAPL",
    prices=[_SNAPSHOT],
    current_price=223.0,
    change_pct_1d=1.5,
    change_pct_5d=-2.3,
    change_pct_1mo=4.1,
    high_52w=237.0,
    low_52w=164.0,
)

_ARTICLE = NewsArticle(
    headline="Apple reports record earnings",
    source="Reuters",
    url="https://reuters.com/apple",
    published_at=datetime(2024, 11, 1, 14, 30),
    summary="Apple beat expectations by 12% driven by services revenue.",
)

_PROFILE = CompanyProfile(
    name="Apple Inc.",
    ticker="AAPL",
    sector="Technology",
    industry="Consumer Electronics",
    market_cap=3_400_000.0,
    country="US",
    exchange="NASDAQ",
)

_FILING = FilingRef(
    form_type="10-K",
    filed_date=date(2024, 11, 1),
    description="Annual Report",
    url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index.htm",
)


# ---------------------------------------------------------------------------
# _format_price_data
# ---------------------------------------------------------------------------


class TestFormatPriceData:
    def test_returns_no_data_message_when_none(self):
        assert _format_price_data(None) == "No price data available."

    def test_includes_current_price(self):
        result = _format_price_data(_PRICE_DATA)
        assert "Current price: $223.00" in result

    def test_includes_1d_change(self):
        result = _format_price_data(_PRICE_DATA)
        assert "1-day change: 1.5%" in result

    def test_includes_5d_change(self):
        result = _format_price_data(_PRICE_DATA)
        assert "5-day change: -2.3%" in result

    def test_includes_52w_high_and_low(self):
        result = _format_price_data(_PRICE_DATA)
        assert "52-week high: $237.00" in result
        assert "52-week low: $164.00" in result

    def test_includes_snapshot_row(self):
        result = _format_price_data(_PRICE_DATA)
        assert "2024-11-01" in result
        assert "Open=$220.00" in result

    def test_omits_optional_fields_when_none(self):
        data = PriceData(
            ticker="AAPL",
            prices=[],
            current_price=100.0,
            change_pct_1d=None,
            high_52w=None,
            low_52w=None,
        )
        result = _format_price_data(data)
        assert "1-day change" not in result
        assert "52-week high" not in result

    def test_limits_snapshots_to_last_10(self):
        snapshots = [
            PriceSnapshot(
                date=date(2024, 1, i + 1),
                open=100.0,
                high=105.0,
                low=98.0,
                close=102.0,
                volume=1_000_000,
            )
            for i in range(15)
        ]
        data = PriceData(ticker="AAPL", prices=snapshots, current_price=102.0)
        result = _format_price_data(data)
        # Only last 10 — first 5 dates should NOT appear
        assert "2024-01-01" not in result
        assert "2024-01-15" in result


# ---------------------------------------------------------------------------
# _format_news
# ---------------------------------------------------------------------------


class TestFormatNews:
    def test_returns_no_news_message_for_empty_list(self):
        assert _format_news([]) == "No recent news available."

    def test_includes_headline(self):
        result = _format_news([_ARTICLE])
        assert "Apple reports record earnings" in result

    def test_includes_source(self):
        result = _format_news([_ARTICLE])
        assert "Reuters" in result

    def test_includes_formatted_date(self):
        result = _format_news([_ARTICLE])
        assert "2024-11-01" in result

    def test_includes_truncated_summary(self):
        long_summary = "x" * 500
        article = NewsArticle(
            headline="Test",
            source="Test",
            url="https://test.com",
            published_at=datetime(2024, 1, 1),
            summary=long_summary,
        )
        result = _format_news([article])
        assert len([line for line in result.split("\n") if "x" in line]) == 1
        # summary truncated to 300 chars
        assert "x" * 300 in result
        assert "x" * 301 not in result

    def test_numbers_articles_sequentially(self):
        articles = [
            NewsArticle(
                headline=f"Story {i}",
                source="CNN",
                url="https://cnn.com",
                published_at=datetime(2024, 1, i),
                summary="",
            )
            for i in range(1, 4)
        ]
        result = _format_news(articles)
        assert "1." in result
        assert "2." in result
        assert "3." in result


# ---------------------------------------------------------------------------
# _format_profile
# ---------------------------------------------------------------------------


class TestFormatProfile:
    def test_returns_no_profile_message_when_none(self):
        assert _format_profile(None) == "No company profile available."

    def test_includes_company_name_and_ticker(self):
        result = _format_profile(_PROFILE)
        assert "Apple Inc." in result
        assert "AAPL" in result

    def test_includes_sector_and_industry(self):
        result = _format_profile(_PROFILE)
        assert "Technology" in result
        assert "Consumer Electronics" in result

    def test_includes_market_cap(self):
        result = _format_profile(_PROFILE)
        assert "3,400,000" in result

    def test_shows_na_for_missing_optional_fields(self):
        profile = CompanyProfile(name="Acme", ticker="ACM")
        result = _format_profile(profile)
        assert "N/A" in result


# ---------------------------------------------------------------------------
# _format_filings
# ---------------------------------------------------------------------------


class TestFormatFilings:
    def test_returns_no_filings_message_for_empty_list(self):
        assert _format_filings([]) == "No SEC filings fetched."

    def test_includes_form_type_and_date(self):
        result = _format_filings([_FILING])
        assert "10-K" in result
        assert "2024-11-01" in result

    def test_includes_description(self):
        result = _format_filings([_FILING])
        assert "Annual Report" in result

    def test_includes_url(self):
        result = _format_filings([_FILING])
        assert "sec.gov" in result


# ---------------------------------------------------------------------------
# gather_evidence (async)
# ---------------------------------------------------------------------------


def _make_request(**kwargs) -> AnalysisRequest:
    defaults = {"ticker": "AAPL", "period": "1mo", "include_filings": False}
    return AnalysisRequest(**{**defaults, **kwargs})


def _make_settings(finnhub_key: str = "test_key"):
    s = MagicMock()
    s.FINNHUB_API_KEY = finnhub_key
    return s


class TestGatherEvidence:
    @pytest.mark.asyncio
    async def test_returns_evidence_bundle_on_success(self):
        price_payload = {
            "ticker": "AAPL",
            "prices": [
                {
                    "date": "2024-11-01",
                    "open": 220.0,
                    "high": 225.0,
                    "low": 219.0,
                    "close": 223.0,
                    "volume": 55_000_000,
                }
            ],
            "current_price": 223.0,
        }
        with (
            patch("app.orchestrator.fetch_price_data") as mock_price,
            patch("app.orchestrator.fetch_news") as mock_news,
            patch("app.orchestrator.fetch_company_profile") as mock_profile,
            patch("app.orchestrator.fetch_recent_filings") as mock_filings,
        ):
            mock_price.invoke.return_value = price_payload
            mock_news.invoke.return_value = []
            mock_profile.invoke.return_value = None
            mock_filings.invoke.return_value = []

            result = await gather_evidence(_make_request(), _make_settings())

        assert isinstance(result, EvidenceBundle)
        assert result.ticker == "AAPL"
        assert result.price_data is not None
        assert result.price_data.current_price == 223.0

    @pytest.mark.asyncio
    async def test_captures_price_error_without_raising(self):
        with (
            patch("app.orchestrator.fetch_price_data") as mock_price,
            patch("app.orchestrator.fetch_news") as mock_news,
            patch("app.orchestrator.fetch_company_profile") as mock_profile,
            patch("app.orchestrator.fetch_recent_filings") as mock_filings,
        ):
            mock_price.invoke.side_effect = Exception("yfinance down")
            mock_news.invoke.return_value = []
            mock_profile.invoke.return_value = None
            mock_filings.invoke.return_value = []

            result = await gather_evidence(_make_request(), _make_settings())

        assert result.price_data is None
        assert any("Price data" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_skips_filings_when_not_requested(self):
        with (
            patch("app.orchestrator.fetch_price_data") as mock_price,
            patch("app.orchestrator.fetch_news") as mock_news,
            patch("app.orchestrator.fetch_company_profile") as mock_profile,
            patch("app.orchestrator.fetch_recent_filings") as mock_filings,
        ):
            mock_price.invoke.return_value = None
            mock_news.invoke.return_value = []
            mock_profile.invoke.return_value = None

            result = await gather_evidence(
                _make_request(include_filings=False), _make_settings()
            )

        mock_filings.invoke.assert_not_called()
        assert result.filings == []

    @pytest.mark.asyncio
    async def test_skips_news_when_no_finnhub_key(self):
        with (
            patch("app.orchestrator.fetch_price_data") as mock_price,
            patch("app.orchestrator.fetch_news") as mock_news,
            patch("app.orchestrator.fetch_company_profile") as mock_profile,
            patch("app.orchestrator.fetch_recent_filings") as mock_filings,
        ):
            mock_price.invoke.return_value = None
            mock_filings.invoke.return_value = []

            result = await gather_evidence(_make_request(), _make_settings(finnhub_key=""))

        mock_news.invoke.assert_not_called()
        assert result.news == []
        assert any("FINNHUB_API_KEY" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_returns_filings_when_requested(self):
        filing_payload = [
            {
                "form_type": "10-K",
                "filed_date": "2024-11-01",
                "description": "Annual Report",
                "url": "https://www.sec.gov/test",
            }
        ]
        with (
            patch("app.orchestrator.fetch_price_data") as mock_price,
            patch("app.orchestrator.fetch_news") as mock_news,
            patch("app.orchestrator.fetch_company_profile") as mock_profile,
            patch("app.orchestrator.fetch_recent_filings") as mock_filings,
        ):
            mock_price.invoke.return_value = None
            mock_news.invoke.return_value = []
            mock_profile.invoke.return_value = None
            mock_filings.invoke.return_value = filing_payload

            result = await gather_evidence(
                _make_request(include_filings=True), _make_settings()
            )

        assert len(result.filings) == 1
        assert result.filings[0].form_type == "10-K"

    @pytest.mark.asyncio
    async def test_multiple_tool_failures_all_captured(self):
        with (
            patch("app.orchestrator.fetch_price_data") as mock_price,
            patch("app.orchestrator.fetch_news") as mock_news,
            patch("app.orchestrator.fetch_company_profile") as mock_profile,
            patch("app.orchestrator.fetch_recent_filings") as mock_filings,
        ):
            mock_price.invoke.side_effect = Exception("price fail")
            mock_news.invoke.side_effect = Exception("news fail")
            mock_profile.invoke.side_effect = Exception("profile fail")
            mock_filings.invoke.return_value = []

            result = await gather_evidence(_make_request(), _make_settings())

        assert result.price_data is None
        assert result.news == []
        assert result.profile is None
        assert len(result.errors) >= 3
