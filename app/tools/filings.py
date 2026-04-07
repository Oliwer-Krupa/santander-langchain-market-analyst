import logging

import httpx
from langchain_core.tools import tool

from app.models.evidence import FilingRef

logger = logging.getLogger(__name__)

SEC_BASE = "https://efts.sec.gov/LATEST/search-index"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions"
SEC_HEADERS = {"User-Agent": "IncidentAnalyst/1.0 contact@example.com"}


def _get_cik(ticker: str) -> str | None:
    """Resolve a ticker to a SEC CIK number."""
    try:
        response = httpx.get(
            "https://www.sec.gov/cgi-bin/browse-edgar",
            params={"action": "getcompany", "company": ticker, "type": "", "output": "atom"},
            headers=SEC_HEADERS,
            timeout=10,
            follow_redirects=True,
        )
        # Try the simpler tickers.json approach
        tickers_resp = httpx.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=SEC_HEADERS,
            timeout=10,
        )
        tickers_resp.raise_for_status()
        data = tickers_resp.json()

        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                return str(entry["cik_str"]).zfill(10)

        return None
    except Exception:
        logger.exception("Failed to resolve CIK for %s", ticker)
        return None


@tool
def fetch_recent_filings(ticker: str, max_filings: int = 10) -> list[dict]:
    """Fetch recent SEC EDGAR filings for a given ticker.

    Returns up to 10 recent filings with form type, date, description, and URL.
    This is an optional data source — returns empty list on failure.
    """
    try:
        cik = _get_cik(ticker)
        if not cik:
            logger.warning("Could not resolve CIK for %s", ticker)
            return []

        response = httpx.get(
            f"{SEC_SUBMISSIONS}/CIK{cik}.json",
            headers=SEC_HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        descriptions = recent.get("primaryDocDescription", [])
        accessions = recent.get("accessionNumber", [])

        filings = []
        for i in range(min(len(forms), max_filings)):
            accession_clean = accessions[i].replace("-", "")
            filing = FilingRef(
                form_type=forms[i],
                filed_date=dates[i],
                description=descriptions[i] if i < len(descriptions) else forms[i],
                url=f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession_clean}/{accessions[i]}-index.htm",
            )
            filings.append(filing.model_dump(mode="json"))

        logger.info("Fetched %d filings for %s", len(filings), ticker)
        return filings

    except Exception:
        logger.exception("Failed to fetch filings for %s", ticker)
        return []
