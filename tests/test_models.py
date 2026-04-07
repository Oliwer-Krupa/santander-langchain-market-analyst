import pytest
from pydantic import ValidationError

from app.models.report import IncidentFactor, IncidentReport, PriceMoveSummary
from app.models.request import AnalysisRequest


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
