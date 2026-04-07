from datetime import date, datetime

from pydantic import BaseModel, Field


class PriceSnapshot(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceData(BaseModel):
    ticker: str
    prices: list[PriceSnapshot]
    current_price: float
    change_pct_1d: float | None = None
    change_pct_5d: float | None = None
    change_pct_1mo: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None


class NewsArticle(BaseModel):
    headline: str
    source: str
    url: str
    published_at: datetime
    summary: str


class CompanyProfile(BaseModel):
    name: str
    ticker: str
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    description: str | None = None
    country: str | None = None
    exchange: str | None = None


class FilingRef(BaseModel):
    form_type: str
    filed_date: date
    description: str
    url: str


class EvidenceBundle(BaseModel):
    """All evidence gathered by the orchestrator, passed to the LLM chain."""

    ticker: str
    price_data: PriceData | None = None
    news: list[NewsArticle] = Field(default_factory=list)
    profile: CompanyProfile | None = None
    filings: list[FilingRef] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
