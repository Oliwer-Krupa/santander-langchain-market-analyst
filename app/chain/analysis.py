from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.chain.prompts import analysis_prompt
from app.models.report import IncidentReport


def build_analysis_chain(llm: ChatOpenAI) -> Runnable:
    """Build the LCEL analysis chain: prompt -> structured LLM output.

    Architecture note:
        This chain receives pre-gathered evidence as formatted strings and
        produces a structured IncidentReport via LangChain's with_structured_output.
        The LLM's role is synthesis and reasoning — not tool selection.
        Tools are called deterministically by the orchestrator before this chain runs.
    """
    structured_llm = llm.with_structured_output(IncidentReport)
    chain = analysis_prompt | structured_llm
    return chain
