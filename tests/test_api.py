from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.models.report import IncidentFactor, IncidentReport, PriceMoveSummary


def _test_settings():
    return Settings(OPENAI_API_KEY="test-key", FINNHUB_API_KEY="test-key")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_report():
    return IncidentReport(
        ticker="AAPL",
        company_name="Apple Inc.",
        executive_summary="Test summary.",
        price_move=PriceMoveSummary(
            direction="up",
            magnitude_pct=5.0,
            timeframe="1 month",
            description="Test price move.",
        ),
        factors=[
            IncidentFactor(
                category="earnings",
                title="Strong Earnings",
                description="Test description.",
                confidence="high",
                supporting_evidence=["Test evidence"],
            ),
        ],
        risk_assessment="Test risk.",
        outlook="Test outlook.",
        data_quality_note="Test note.",
    )


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestAnalyzeEndpoint:
    def test_invalid_ticker_returns_422(self, client):
        response = client.post("/analyze", json={"ticker": "invalid"})
        assert response.status_code == 422

    def test_empty_ticker_returns_422(self, client):
        response = client.post("/analyze", json={"ticker": ""})
        assert response.status_code == 422

    @patch("app.api.routes.analyze")
    @patch("app.api.routes.get_settings", side_effect=_test_settings)
    def test_valid_request_returns_report(self, mock_settings, mock_analyze, client, mock_report):
        mock_analyze.return_value = mock_report

        response = client.post("/analyze", json={"ticker": "AAPL"})
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["company_name"] == "Apple Inc."
        assert len(data["factors"]) == 1

    @patch("app.api.routes.analyze")
    @patch("app.api.routes.get_settings", side_effect=_test_settings)
    def test_request_with_options(self, mock_settings, mock_analyze, client, mock_report):
        mock_analyze.return_value = mock_report

        response = client.post(
            "/analyze",
            json={
                "ticker": "NVDA",
                "query": "Why did it drop?",
                "period": "1mo",
                "include_filings": True,
            },
        )
        assert response.status_code == 200
