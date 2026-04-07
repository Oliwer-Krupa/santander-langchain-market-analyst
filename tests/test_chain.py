from unittest.mock import MagicMock, patch

from app.chain.analysis import build_analysis_chain
from app.chain.prompts import analysis_prompt
from app.models.report import IncidentReport


class TestPrompt:
    def test_prompt_renders(self):
        """Verify prompt template accepts all expected variables."""
        messages = analysis_prompt.format_messages(
            ticker="AAPL",
            profile="Apple Inc. (AAPL)\nSector: Technology",
            price_data="Current price: $210.00\n1-day change: +1.5%",
            news="1. [2024-01-25] Apple Reports Record Revenue",
            filings="No SEC filings fetched.",
            errors="All data sources responded successfully.",
            user_query="Why did AAPL go up?",
        )
        assert len(messages) == 2
        assert "AAPL" in messages[1].content
        assert "senior equity research analyst" in messages[0].content


class TestAnalysisChain:
    def test_chain_structure(self):
        """Verify the chain is built with correct structure."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        chain = build_analysis_chain(mock_llm)

        mock_llm.with_structured_output.assert_called_once_with(IncidentReport)
        assert chain is not None
