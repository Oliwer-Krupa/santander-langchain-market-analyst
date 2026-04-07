import pytest

from app.config import Settings
from app.models.evidence import (
    CompanyProfile,
    EvidenceBundle,
    NewsArticle,
    PriceData,
    PriceSnapshot,
)
from app.models.report import IncidentFactor, IncidentReport, PriceMoveSummary


@pytest.fixture
def sample_settings():
    return Settings(
        OPENAI_API_KEY="test-key",
        OPENAI_MODEL="gpt-4o-mini",
        FINNHUB_API_KEY="test-finnhub-key",
    )


@pytest.fixture
def sample_price_data():
    from datetime import date

    return PriceData(
        ticker="AAPL",
        prices=[
            PriceSnapshot(
                date=date(2024, 1, i + 1),
                open=180.0 + i,
                high=182.0 + i,
                low=179.0 + i,
                close=181.0 + i,
                volume=50000000 + i * 1000000,
            )
            for i in range(30)
        ],
        current_price=210.0,
        change_pct_1d=1.5,
        change_pct_5d=-3.2,
        change_pct_1mo=5.0,
        high_52w=230.0,
        low_52w=160.0,
    )


@pytest.fixture
def sample_news():
    from datetime import datetime

    return [
        NewsArticle(
            headline="Apple Reports Record Quarterly Revenue",
            source="Reuters",
            url="https://example.com/article1",
            published_at=datetime(2024, 1, 25, 14, 30),
            summary="Apple Inc. reported quarterly revenue of $120B, beating estimates.",
        ),
        NewsArticle(
            headline="iPhone Sales Exceed Expectations in China",
            source="Bloomberg",
            url="https://example.com/article2",
            published_at=datetime(2024, 1, 24, 10, 0),
            summary="iPhone sales in China grew 15% YoY in Q4.",
        ),
    ]


@pytest.fixture
def sample_profile():
    return CompanyProfile(
        name="Apple Inc.",
        ticker="AAPL",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3000000.0,
        country="US",
        exchange="NASDAQ",
    )


@pytest.fixture
def sample_evidence(sample_price_data, sample_news, sample_profile):
    return EvidenceBundle(
        ticker="AAPL",
        price_data=sample_price_data,
        news=sample_news,
        profile=sample_profile,
        filings=[],
        errors=[],
    )


@pytest.fixture
def sample_report():
    return IncidentReport(
        ticker="AAPL",
        company_name="Apple Inc.",
        executive_summary="Apple stock rose 5% over the past month driven by strong Q4 earnings and robust iPhone sales in China.",
        price_move=PriceMoveSummary(
            direction="up",
            magnitude_pct=5.0,
            timeframe="1 month",
            description="AAPL gained 5% over the past month.",
        ),
        factors=[
            IncidentFactor(
                category="earnings",
                title="Record Q4 Revenue",
                description="Apple reported record quarterly revenue of $120B, beating analyst estimates.",
                confidence="high",
                supporting_evidence=["Reuters: Apple Reports Record Quarterly Revenue"],
            ),
        ],
        risk_assessment="Valuation is elevated relative to historical averages.",
        outlook="Positive near-term momentum supported by strong fundamentals.",
        data_quality_note="All data sources responded successfully.",
    )
