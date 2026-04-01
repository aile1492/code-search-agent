"""LangGraph graph definition for the Code Search Agent."""

import asyncio
from langgraph.graph import StateGraph, START, END
from app.agent.state import SearchState
from app.agent.nodes import search_node, rerank_node, answer_node


def build_graph():
    """Build the Code Search Agent graph.

    Flow: START → search → rerank → answer → END
    """
    graph = StateGraph(SearchState)

    graph.add_node("search", search_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("answer", answer_node)

    graph.add_edge(START, "search")
    graph.add_edge("search", "rerank")
    graph.add_edge("rerank", "answer")
    graph.add_edge("answer", END)

    return graph.compile()


# Compiled graph instance
search_graph = build_graph()


async def run_search_graph(
    query: str,
    project: str,
    session_id: str,
    queue: asyncio.Queue,
    history: list[dict] | None = None,
    provider: str | None = None,
    api_key: str | None = None,
):
    """Run the search graph with SSE event streaming."""
    initial_state = {
        "query": query,
        "project": project,
        "search_results": [],
        "reranked_results": [],
        "expanded_context": [],
        "answer": "",
        "conversation_history": history or [],
        "current_step": "",
        "error": "",
        "_queue": queue,
        "_session_id": session_id,
        "_provider": provider or "",
        "_api_key": api_key or "",
    }

    await search_graph.ainvoke(initial_state)


if __name__ == "__main__":
    import sys

    async def test():
        q = asyncio.Queue()

        async def printer():
            while True:
                event = await q.get()
                if event is None:
                    break
                print(f"[{event.get('type')}] {json.dumps(event, ensure_ascii=False, default=str)[:200]}")

        import json
        task = asyncio.create_task(printer())
        query = sys.argv[1] if len(sys.argv) > 1 else "main function"
        project = sys.argv[2] if len(sys.argv) > 2 else None

        try:
            await run_search_graph(query, project or "", "test", q)
        finally:
            await q.put(None)
            await task

    asyncio.run(test())
