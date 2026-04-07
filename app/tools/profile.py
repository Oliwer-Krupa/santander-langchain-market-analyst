import logging

import httpx
from langchain_core.tools import tool

from app.models.evidence import CompanyProfile

logger = logging.getLogger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"


@tool
def fetch_company_profile(ticker: str, finnhub_api_key: str) -> dict | None:
    """Fetch company profile information from Finnhub.

    Returns company name, sector, industry, market cap, and description.
    """
    try:
        response = httpx.get(
            f"{FINNHUB_BASE}/stock/profile2",
            params={"symbol": ticker, "token": finnhub_api_key},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        if not data or "name" not in data:
            logger.warning("No profile data returned for %s", ticker)
            return None

        profile = CompanyProfile(
            name=data.get("name", ticker),
            ticker=data.get("ticker", ticker),
            sector=data.get("finnhubIndustry"),
            industry=data.get("finnhubIndustry"),
            market_cap=data.get("marketCapitalization"),
            country=data.get("country"),
            exchange=data.get("exchange"),
        )

        logger.info("Fetched profile for %s: %s", ticker, profile.name)
        return profile.model_dump()

    except Exception:
        logger.exception("Failed to fetch profile for %s", ticker)
        return None
