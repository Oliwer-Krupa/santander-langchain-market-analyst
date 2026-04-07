import logging

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.report import IncidentReport
from app.models.request import AnalysisRequest
from app.orchestrator import analyze

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=IncidentReport)
async def analyze_ticker(request: AnalysisRequest):
    """Analyze a stock ticker and generate an incident report.

    Gathers price data, news, company profile, and optionally SEC filings,
    then synthesizes the evidence into a structured analyst report.
    """
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    try:
        report = await analyze(request, settings)
        return report
    except Exception as e:
        logger.exception("Analysis failed for %s", request.ticker)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "model": settings.OPENAI_MODEL,
        "finnhub_configured": bool(settings.FINNHUB_API_KEY),
    }
