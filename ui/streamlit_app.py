"""Streamlit UI for Market Incident Analyst.

Can run in two modes:
- API mode: calls the FastAPI backend (default when backend is running)
- Direct mode: calls the orchestrator directly (simpler for local dev)
"""

import json
import os

import httpx
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Market Incident Analyst",
    page_icon="📊",
    layout="wide",
)

# In Docker Compose, the backend service is reachable at http://backend:8000
API_URL = os.environ.get("API_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Settings")
    mode = st.radio(
        "Backend mode",
        ["API (FastAPI)", "Direct (in-process)"],
        help="API mode requires the FastAPI server to be running.",
    )
    st.divider()
    st.markdown(
        "**Market Incident Analyst** v0.1.0\n\n"
        "Analyzes stock tickers and generates structured incident reports "
        "explaining recent price movements."
    )

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("📊 Market Incident Analyst")
st.caption("AI-powered analysis of unusual stock price movements")

# ---------------------------------------------------------------------------
# Input form
# ---------------------------------------------------------------------------
col1, col2 = st.columns([1, 2])

with col1:
    ticker = st.text_input(
        "Stock Ticker",
        value="",
        placeholder="e.g. AAPL",
        max_chars=5,
        help="Enter a US stock ticker symbol (1-5 uppercase letters)",
    ).upper().strip()

with col2:
    query = st.text_input(
        "Question (optional)",
        value="",
        placeholder="e.g. Why is this stock moving?",
    )

col3, col4 = st.columns([1, 2])

with col3:
    period = st.selectbox(
        "Lookback period",
        ["1mo", "3mo", "6mo", "1y"],
        index=1,
    )

with col4:
    include_filings = st.checkbox("Include SEC filings (slower)", value=False)

analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def call_api(ticker: str, query: str, period: str, include_filings: bool) -> dict:
    payload = {
        "ticker": ticker,
        "period": period,
        "include_filings": include_filings,
    }
    if query:
        payload["query"] = query

    resp = httpx.post(f"{API_URL}/analyze", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def call_direct(ticker: str, query: str, period: str, include_filings: bool) -> dict:
    import asyncio
    from app.config import get_settings
    from app.models.request import AnalysisRequest
    from app.orchestrator import analyze

    request = AnalysisRequest(
        ticker=ticker,
        query=query or None,
        period=period,
        include_filings=include_filings,
    )
    settings = get_settings()
    report = asyncio.run(analyze(request, settings))
    return report.model_dump(mode="json")


if analyze_btn:
    if not ticker or not ticker.isalpha() or len(ticker) > 5:
        st.error("Please enter a valid ticker symbol (1-5 uppercase letters).")
    else:
        with st.spinner("Gathering evidence and analyzing..."):
            try:
                if mode == "API (FastAPI)":
                    report = call_api(ticker, query, period, include_filings)
                else:
                    report = call_direct(ticker, query, period, include_filings)

                st.session_state["report"] = report
            except httpx.ConnectError:
                st.error(
                    "Could not connect to the API server. "
                    "Make sure the FastAPI backend is running on port 8000, "
                    "or switch to Direct mode in the sidebar."
                )
            except Exception as e:
                st.error(f"Analysis failed: {e}")


# ---------------------------------------------------------------------------
# Report display
# ---------------------------------------------------------------------------
if "report" in st.session_state:
    report = st.session_state["report"]

    st.divider()

    # Header
    st.header(f"{report['ticker']} — {report.get('company_name', 'Unknown')}")
    st.caption(f"Generated: {report.get('generated_at', 'N/A')}")

    # Executive summary
    st.subheader("Executive Summary")
    st.info(report.get("executive_summary", ""))

    # Price move
    col_a, col_b = st.columns([1, 2])

    price_move = report.get("price_move", {})
    with col_a:
        direction = price_move.get("direction", "flat")
        magnitude = price_move.get("magnitude_pct", 0)
        color = "🟢" if direction == "up" else "🔴" if direction == "down" else "⚪"
        st.metric(
            label="Price Move",
            value=f"{magnitude:+.1f}%",
            delta=f"{direction.upper()} over {price_move.get('timeframe', 'N/A')}",
            delta_color="normal" if direction == "up" else "inverse" if direction == "down" else "off",
        )

    with col_b:
        st.markdown(f"**Details:** {price_move.get('description', 'N/A')}")

    # Contributing factors
    st.subheader("Contributing Factors")

    factors = report.get("factors", [])
    if factors:
        for i, factor in enumerate(factors, 1):
            confidence = factor.get("confidence", "low")
            badge_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(confidence, "⚪")

            with st.expander(
                f"{i}. {factor.get('title', 'Unknown')} — {badge_color} {confidence.upper()} confidence",
                expanded=(i <= 2),
            ):
                st.markdown(f"**Category:** `{factor.get('category', 'other')}`")
                st.markdown(factor.get("description", ""))
                evidence_items = factor.get("supporting_evidence", [])
                if evidence_items:
                    st.markdown("**Supporting evidence:**")
                    for ev in evidence_items:
                        st.markdown(f"- {ev}")
    else:
        st.warning("No contributing factors identified.")

    # Risk assessment & outlook
    col_r, col_o = st.columns(2)

    with col_r:
        st.subheader("Risk Assessment")
        st.warning(report.get("risk_assessment", "N/A"))

    with col_o:
        st.subheader("Outlook")
        st.success(report.get("outlook", "N/A"))

    # Data quality
    st.subheader("Data Quality Note")
    st.caption(report.get("data_quality_note", "N/A"))

    # Download
    st.divider()
    st.download_button(
        label="📥 Download Report (JSON)",
        data=json.dumps(report, indent=2, default=str),
        file_name=f"incident_report_{report['ticker']}.json",
        mime="application/json",
    )
