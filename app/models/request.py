from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    ticker: str = Field(
        ...,
        pattern=r"^[A-Z]{1,5}$",
        description="Stock ticker symbol (e.g. AAPL, NVDA)",
        examples=["AAPL", "NVDA", "TSLA"],
    )
    query: str | None = Field(
        None,
        description="Optional question to focus the analysis, e.g. 'Why did this stock drop?'",
    )
    period: str = Field(
        "3mo",
        description="Price history lookback period (yfinance format: 1mo, 3mo, 6mo, 1y)",
    )
    include_filings: bool = Field(
        False,
        description="Whether to fetch recent SEC filings",
    )
