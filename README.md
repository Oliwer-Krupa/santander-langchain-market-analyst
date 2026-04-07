# Market Incident Analyst

AI-powered stock incident analysis that explains unusual price movements by combining market data, news, and LLM reasoning into structured analyst reports.

## Why This Project

Most AI demos wrap a single prompt. This project demonstrates a **production-like architecture** where:

- **LangChain orchestrates** a multi-step analysis pipeline with tools, structured output, and prompt engineering
- **Deterministic orchestration** (not a ReAct agent) ensures reliability while still showcasing LangChain's tool and chain patterns
- **Graceful degradation** means partial data doesn't crash the system — the LLM works with what's available
- **Pydantic schemas** enforce structure at every boundary: API input, evidence models, and LLM output

## Architecture

```
User Input (ticker + optional query)
       │
       ▼
┌─────────────────────────────────────────┐
│           FastAPI Backend               │
│                                         │
│  ┌─────────────┐                        │
│  │ Orchestrator │─── gather_evidence()  │
│  │              │    ├── price_tool     │  ← yfinance
│  │              │    ├── news_tool      │  ← Finnhub
│  │              │    ├── profile_tool   │  ← Finnhub
│  │              │    └── filings_tool   │  ← SEC EDGAR
│  │              │                       │
│  │              │─── analyze()          │
│  │              │    └── LCEL Chain     │
│  │              │        prompt │       │
│  │              │        structured_llm │  ← OpenAI
│  └──────┬──────┘        ↓              │
│         │         IncidentReport        │
│         ▼         (Pydantic)            │
│    POST /analyze                        │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────┐
│   Streamlit UI      │
│   - Executive       │
│     summary         │
│   - Price chart     │
│   - Factors ranked  │
│   - Risk + Outlook  │
│   - Download JSON   │
└─────────────────────┘
```

### Why Deterministic Orchestration Over an Agent

The tool-calling sequence is **known at design time** — we always need price data, news, and a profile. A ReAct agent would add:
- Extra LLM calls for "thinking" about which tools to use
- Unpredictable tool ordering and potential hallucinated tool names
- Higher latency and cost

Instead, the **orchestrator calls tools in parallel** via `asyncio.gather`, then passes all evidence to a single LLM call for synthesis. The LLM does what it's best at (reasoning), not what it's worst at (reliable function dispatch).

The tools are still proper LangChain `@tool`-decorated functions — they could be bound to an agent in a future iteration.

### LangChain Usage

| Feature | Where | Purpose |
|---------|-------|---------|
| `@tool` decorator | `app/tools/*.py` | Defines tools with auto-generated schemas |
| `ChatPromptTemplate` | `app/chain/prompts.py` | System + human message templates |
| `with_structured_output` | `app/chain/analysis.py` | Forces Pydantic-typed LLM responses |
| LCEL pipe (`\|`) | `app/chain/analysis.py` | Composes prompt → structured LLM |

## Setup

### Prerequisites
- Python 3.11+ (or Docker)
- API keys for OpenAI and Finnhub (free tier)

### Installation

```bash
# Clone and enter project
cd incident-analyst

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running

**Option 1: Full stack (backend + UI)**
```bash
bash run.sh
```

**Option 2: Backend only**
```bash
uvicorn app.main:app --reload --port 8000
```

**Option 3: UI in direct mode (no backend needed)**

```bash
streamlit run ui/streamlit_app.py
# Then select "Direct (in-process)" mode in the sidebar
```

**Option 4: Docker Compose (recommended)**

```bash
# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Build and run both services
docker compose up --build

# Backend: http://localhost:8000
# UI:      http://localhost:8501
```

## API Usage

### POST /analyze

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "NVDA",
    "query": "Why did this stock move recently?",
    "period": "3mo",
    "include_filings": false
  }'
```

**Response** (abridged):
```json
{
  "ticker": "NVDA",
  "company_name": "NVIDIA Corporation",
  "executive_summary": "NVDA declined 8.2% over 5 trading days...",
  "price_move": {
    "direction": "down",
    "magnitude_pct": -8.2,
    "timeframe": "5 trading days",
    "description": "Sharp selloff following..."
  },
  "factors": [
    {
      "category": "earnings",
      "title": "Guidance Miss",
      "description": "...",
      "confidence": "high",
      "supporting_evidence": ["..."]
    }
  ],
  "risk_assessment": "...",
  "outlook": "...",
  "data_quality_note": "All data sources responded successfully."
}
```

### GET /health

```bash
curl http://localhost:8000/health
```

## Testing

```bash
pytest tests/ -v
```

## Screenshots

<!-- Add screenshots of the Streamlit UI here -->

## Project Structure

```
app/
├── main.py              # FastAPI app
├── config.py            # Settings via pydantic-settings
├── orchestrator.py      # Pipeline: gather evidence → analyze
├── models/              # Pydantic schemas
│   ├── request.py       # API input validation
│   ├── evidence.py      # Internal evidence types
│   └── report.py        # Structured LLM output
├── tools/               # LangChain @tool functions
│   ├── price.py         # yfinance
│   ├── news.py          # Finnhub
│   ├── profile.py       # Finnhub
│   └── filings.py       # SEC EDGAR
├── chain/               # LangChain chain
│   ├── llm.py           # LLM factory
│   ├── prompts.py       # Prompt templates
│   └── analysis.py      # LCEL chain definition
└── api/
    └── routes.py        # FastAPI endpoints
```

## Limitations

- **Data freshness**: yfinance data may be delayed 15-20 minutes
- **News coverage**: Finnhub free tier may miss some sources
- **LLM reasoning**: The analysis is only as good as the evidence provided — the model cannot access information beyond what the tools fetch
- **Rate limits**: Finnhub free tier allows 60 requests/minute
- **No persistent storage**: Reports are generated on-the-fly, not stored

## Production Improvements

If this were a production system, I would add:

- **Caching layer** (Redis) for API responses to reduce external calls
- **Background job queue** (Celery/RQ) for async analysis with status polling
- **Vector store** (Pinecone/Chroma) for historical report search and comparison
- **Rate limiting** middleware on the API
- **Authentication** for multi-user scenarios
- **Monitoring** (structured logging, OpenTelemetry traces, LangSmith for chain debugging)
- **More data sources**: Bloomberg, Reuters, social sentiment, options flow
- **Agentic mode**: Let the LLM decide which tools to call based on the query
- **Streaming**: Stream the analysis as it's generated for better UX
