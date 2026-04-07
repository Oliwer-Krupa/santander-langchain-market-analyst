from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.models.evidence import EvidenceBundle, PriceSnapshot
from app.models.report import IncidentFactor, IncidentReport, PriceMoveSummary
from app.models.request import AnalysisRequest


class TestPriceSnapshot:
    def test_accepts_valid_snapshot(self):
        snap = PriceSnapshot(
            date=date(2024, 1, 15),
            open=180.0,
            high=185.0,
            low=179.0,
            close=183.0,
            volume=50_000_000,
        )
        assert snap.close == 183.0

    def test_rejects_non_integer_volume(self):
        with pytest.raises(ValidationError):
            PriceSnapshot(
                date=date(2024, 1, 15),
                open=180.0,
                high=185.0,
                low=179.0,
                close=183.0,
                volume="not_an_int",
            )


class TestEvidenceBundle:
    def test_defaults_to_empty_lists(self):
        bundle = EvidenceBundle(ticker="AAPL")
        assert bundle.news == []
        assert bundle.filings == []
        assert bundle.errors == []

    def test_price_data_defaults_to_none(self):
        bundle = EvidenceBundle(ticker="AAPL")
        assert bundle.price_data is None
        assert bundle.profile is None

    def test_ticker_is_stored(self):
        bundle = EvidenceBundle(ticker="MSFT")
        assert bundle.ticker == "MSFT"


class TestAnalysisRequest:
    def test_valid_ticker(self):
        req = AnalysisRequest(ticker="AAPL")
        assert req.ticker == "AAPL"
        assert req.period == "3mo"
        assert req.query is None

    def test_ticker_with_query(self):
        req = AnalysisRequest(ticker="NVDA", query="Why did it drop?")
        assert req.query == "Why did it drop?"

    def test_invalid_ticker_lowercase(self):
        with pytest.raises(ValidationError):
            AnalysisRequest(ticker="aapl")

    def test_invalid_ticker_too_long(self):
        with pytest.raises(ValidationError):
            AnalysisRequest(ticker="TOOLONG")

    def test_invalid_ticker_numbers(self):
        with pytest.raises(ValidationError):
            AnalysisRequest(ticker="AAP1")


class TestIncidentReport:
    def test_valid_report(self, sample_report):
        assert sample_report.ticker == "AAPL"
        assert len(sample_report.factors) >= 1

    def test_report_requires_factors(self):
        with pytest.raises(ValidationError):
            IncidentReport(
                ticker="AAPL",
                company_name="Apple",
                executive_summary="Test",
                price_move=PriceMoveSummary(
                    direction="up",
                    magnitude_pct=1.0,
                    timeframe="1 day",
                    description="test",
                ),
                factors=[],  # min_length=1
                risk_assessment="test",
                outlook="test",
                data_quality_note="test",
            )

    def test_factor_confidence_validation(self):
        with pytest.raises(ValidationError):
            IncidentFactor(
                category="earnings",
                title="Test",
                description="Test",
                confidence="very_high",  # invalid
                supporting_evidence=["test"],
            )

    def test_factor_category_validation(self):
        with pytest.raises(ValidationError):
            IncidentFactor(
                category="unknown_category",  # invalid
                title="Test",
                description="Test",
                confidence="high",
                supporting_evidence=["test"],
            )
