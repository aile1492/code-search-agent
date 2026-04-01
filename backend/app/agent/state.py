"""LangGraph state schema for the Code Search Agent."""

import asyncio
from typing import Annotated, TypedDict
from operator import add


class SearchState(TypedDict):
    query: str                              # user's natural language question
    project: str                            # project name to search in
    search_results: list[dict]              # raw vector search results
    reranked_results: list[dict]            # LLM-filtered/reranked results
    expanded_context: list[dict]            # results with surrounding context
    answer: str                             # final LLM-generated answer
    conversation_history: Annotated[list[dict], add]  # chat history
    current_step: str                       # UI: "searching" | "reranking" | "expanding" | "answering"
    error: str                              # error message if any
    _queue: asyncio.Queue                   # SSE event queue
    _session_id: str
    _provider: str                          # "gemini" | "anthropic" | "groq"
    _api_key: str                           # user-provided or server-default API key
