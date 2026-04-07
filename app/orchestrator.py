"""Orchestrator — deterministic pipeline that gathers evidence and runs analysis.

Design decision:
    Tools are called in parallel by the orchestrator, NOT by an LLM agent.
    This gives us predictable latency, reliable execution, and easy testing.
    The LLM only does what it's best at: synthesizing evidence into insight.
"""

import asyncio
import logging
from datetime import datetime

from app.chain.analysis import build_analysis_chain
from app.chain.llm import get_llm
from app.config import Settings
from app.models.evidence import (
    CompanyProfile,
    EvidenceBundle,
    FilingRef,
    NewsArticle,
    PriceData,
)
from app.models.report import IncidentReport
from app.models.request import AnalysisRequest
from app.tools.filings import fetch_recent_filings
from app.tools.news import fetch_news
from app.tools.price import fetch_price_data
from app.tools.profile import fetch_company_profile

logger = logging.getLogger(__name__)


async def _run_in_executor(func, *args):
    """Run a sync tool function in a thread executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func.invoke({"ticker": args[0], **{k: v for k, v in zip(func.args.keys(), args) if k != "ticker"}} if len(args) > 1 else {"ticker": args[0]}))


async def gather_evidence(request: AnalysisRequest, settings: Settings) -> EvidenceBundle:
    """Gather all evidence in parallel. Individual failures are captured, not raised."""
    loop = asyncio.get_event_loop()
    errors: list[str] = []

    # Define tool calls as sync lambdas to run in executor
    async def safe_price() -> PriceData | None:
        try:
            result = await loop.run_in_executor(
                None,
                lambda: fetch_price_data.invoke(
                    {"ticker": request.ticker, "period": request.period}
                ),
            )
            if result:
                return PriceData(**result)
            errors.append("Price data: no data returned")
            return None
        except Exception as e:
            errors.append(f"Price data: {e}")
            logger.exception("Price tool failed for %s", request.ticker)
            return None

    async def safe_news() -> list[NewsArticle]:
        try:
            if not settings.FINNHUB_API_KEY:
                errors.append("News: FINNHUB_API_KEY not configured")
                return []
            result = await loop.run_in_executor(
                None,
                lambda: fetch_news.invoke(
                    {"ticker": request.ticker, "finnhub_api_key": settings.FINNHUB_API_KEY}
                ),
            )
            return [NewsArticle(**a) for a in result] if result else []
        except Exception as e:
            errors.append(f"News: {e}")
            logger.exception("News tool failed for %s", request.ticker)
            return []

    async def safe_profile() -> CompanyProfile | None:
        try:
            if not settings.FINNHUB_API_KEY:
                errors.append("Profile: FINNHUB_API_KEY not configured")
                return None
            result = await loop.run_in_executor(
                None,
                lambda: fetch_company_profile.invoke(
                    {"ticker": request.ticker, "finnhub_api_key": settings.FINNHUB_API_KEY}
                ),
            )
            if result:
                return CompanyProfile(**result)
            errors.append("Profile: no data returned")
            return None
        except Exception as e:
            errors.append(f"Profile: {e}")
            logger.exception("Profile tool failed for %s", request.ticker)
            return None

    async def safe_filings() -> list[FilingRef]:
        if not request.include_filings:
            return []
        try:
            result = await loop.run_in_executor(
                None,
                lambda: fetch_recent_filings.invoke({"ticker": request.ticker}),
            )
            return [FilingRef(**f) for f in result] if result else []
        except Exception as e:
            errors.append(f"Filings: {e}")
            logger.exception("Filings tool failed for %s", request.ticker)
            return []

    # Run all tools in parallel
    price_data, news, profile, filings = await asyncio.gather(
        safe_price(), safe_news(), safe_profile(), safe_filings()
    )

    return EvidenceBundle(
        ticker=request.ticker,
        price_data=price_data,
        news=news,
        profile=profile,
        filings=filings,
        errors=errors,
    )


def _format_price_data(data: PriceData | None) -> str:
    if not data:
        return "No price data available."

    lines = [
        f"Current price: ${data.current_price:.2f}",
        f"1-day change: {data.change_pct_1d}%" if data.change_pct_1d is not None else "",
        f"5-day change: {data.change_pct_5d}%" if data.change_pct_5d is not None else "",
        f"1-month change: {data.change_pct_1mo}%" if data.change_pct_1mo is not None else "",
        f"52-week high: ${data.high_52w:.2f}" if data.high_52w else "",
        f"52-week low: ${data.low_52w:.2f}" if data.low_52w else "",
        "",
        "Recent prices (last 10 trading days):",
    ]

    for snap in data.prices[-10:]:
        lines.append(
            f"  {snap.date}: Open=${snap.open:.2f} High=${snap.high:.2f} "
            f"Low=${snap.low:.2f} Close=${snap.close:.2f} Vol={snap.volume:,}"
        )

    return "\n".join(line for line in lines if line or line == "")


def _format_news(articles: list[NewsArticle]) -> str:
    if not articles:
        return "No recent news available."

    lines = []
    for i, article in enumerate(articles, 1):
        lines.append(f"{i}. [{article.published_at.strftime('%Y-%m-%d')}] {article.headline}")
        lines.append(f"   Source: {article.source}")
        if article.summary:
            lines.append(f"   Summary: {article.summary[:300]}")
        lines.append("")

    return "\n".join(lines)


def _format_profile(profile: CompanyProfile | None) -> str:
    if not profile:
        return "No company profile available."

    lines = [
        f"Company: {profile.name} ({profile.ticker})",
        f"Sector: {profile.sector or 'N/A'}",
        f"Industry: {profile.industry or 'N/A'}",
        f"Market Cap: ${profile.market_cap:,.0f}M" if profile.market_cap else "Market Cap: N/A",
        f"Country: {profile.country or 'N/A'}",
        f"Exchange: {profile.exchange or 'N/A'}",
    ]
    return "\n".join(lines)


def _format_filings(filings: list[FilingRef]) -> str:
    if not filings:
        return "No SEC filings fetched."

    lines = []
    for f in filings:
        lines.append(f"- {f.form_type} ({f.filed_date}): {f.description}")
        lines.append(f"  URL: {f.url}")
    return "\n".join(lines)


async def analyze(request: AnalysisRequest, settings: Settings) -> IncidentReport:
    """Full analysis pipeline: gather evidence -> format -> LLM chain -> report."""

    logger.info("Starting analysis for %s", request.ticker)

    # Step 1: Gather evidence from all sources
    evidence = await gather_evidence(request, settings)

    logger.info(
        "Evidence gathered for %s: price=%s, news=%d, profile=%s, filings=%d, errors=%d",
        request.ticker,
        evidence.price_data is not None,
        len(evidence.news),
        evidence.profile is not None,
        len(evidence.filings),
        len(evidence.errors),
    )

    # Step 2: Format evidence for the prompt
    chain_input = {
        "ticker": request.ticker,
        "profile": _format_profile(evidence.profile),
        "price_data": _format_price_data(evidence.price_data),
        "news": _format_news(evidence.news),
        "filings": _format_filings(evidence.filings),
        "errors": "\n".join(evidence.errors) if evidence.errors else "All data sources responded successfully.",
        "user_query": request.query or "What caused the recent price movement for this stock?",
    }

    # Step 3: Run the LangChain analysis chain
    llm = get_llm(settings)
    chain = build_analysis_chain(llm)

    logger.info("Invoking analysis chain for %s", request.ticker)
    report = await asyncio.get_event_loop().run_in_executor(
        None, lambda: chain.invoke(chain_input)
    )

    logger.info("Analysis complete for %s", request.ticker)
    return report
