from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PriceMoveSummary(BaseModel):
    direction: Literal["up", "down", "flat"]
    magnitude_pct: float = Field(..., description="Percentage change (positive = up)")
    timeframe: str = Field(..., description="e.g. '5 trading days', '1 month'")
    description: str = Field(..., description="Human-readable summary of the move")


class IncidentFactor(BaseModel):
    category: Literal[
        "earnings", "guidance", "macro", "sector",
        "regulatory", "technical", "sentiment", "other",
    ]
    title: str
    description: str
    confidence: Literal["high", "medium", "low"]
    supporting_evidence: list[str] = Field(
        ...,
        description="Specific data points or news items that support this factor",
    )


class IncidentReport(BaseModel):
    """Structured incident report — the main deliverable of the analysis pipeline."""

    ticker: str
    company_name: str
    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp of when the report was generated",
    )
    executive_summary: str = Field(
        ...,
        description="2-3 sentence summary of what happened and why",
    )
    price_move: PriceMoveSummary
    factors: list[IncidentFactor] = Field(
        ...,
        min_length=1,
        description="Ranked list of factors that may explain the price movement",
    )
    risk_assessment: str = Field(
        ...,
        description="Assessment of ongoing risks related to the identified factors",
    )
    outlook: str = Field(
        ...,
        description="Short-term outlook based on the analysis",
    )
    data_quality_note: str = Field(
        ...,
        description="Note any missing data sources, caveats, or limitations",
    )
