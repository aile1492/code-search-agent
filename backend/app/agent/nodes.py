"""Node implementations for the Code Search Agent graph."""

import json
import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import ANTHROPIC_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, DEFAULT_PROVIDER
from app.indexer.index_manager import search_code
from app.agent.prompts import RERANKER_PROMPT, ANSWER_PROMPT, CONVERSATION_PROMPT

# Provider → model defaults
PROVIDER_MODELS = {
    "gemini": "gemini-2.0-flash",
    "anthropic": "claude-sonnet-4-20250514",
    "groq": "llama-3.3-70b-versatile",
}

# Provider → server-side default API key
PROVIDER_SERVER_KEYS = {
    "gemini": GEMINI_API_KEY,
    "anthropic": ANTHROPIC_API_KEY,
    "groq": GROQ_API_KEY,
}


def get_llm(provider: str, api_key: str, streaming: bool = False):
    """Create LLM instance for the given provider and API key."""
    model = PROVIDER_MODELS.get(provider, PROVIDER_MODELS["gemini"])

    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            streaming=streaming,
            max_tokens=4096,
            temperature=0.2,
        )
    elif provider == "groq":
        return ChatGroq(
            model=model,
            groq_api_key=api_key,
            streaming=streaming,
            max_tokens=4096,
            temperature=0.2,
        )
    else:  # gemini (default)
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            streaming=streaming,
            max_output_tokens=4096,
            temperature=0.2,
        )


def resolve_provider_and_key(state: dict) -> tuple[str, str]:
    """Resolve the provider and API key from state, falling back to server defaults."""
    provider = state.get("_provider") or DEFAULT_PROVIDER
    api_key = state.get("_api_key") or ""

    # If no user key, use server default for this provider
    if not api_key:
        api_key = PROVIDER_SERVER_KEYS.get(provider, "")

    if not api_key:
        raise ValueError(
            f"No API key available for provider '{provider}'. "
            "Please provide your own API key or set the server default."
        )

    return provider, api_key


async def llm_invoke_with_retry(llm, messages, max_retries=3):
    """Invoke LLM with retry logic for transient errors."""
    for attempt in range(max_retries):
        try:
            return await llm.ainvoke(messages)
        except Exception as e:
            error_str = str(e)
            if ("529" in error_str or "overloaded" in error_str.lower()
                    or "429" in error_str or "rate" in error_str.lower()):
                wait = 5 * (attempt + 1)
                await asyncio.sleep(wait)
                if attempt == max_retries - 1:
                    raise
            else:
                raise


async def search_node(state: dict) -> dict:
    """Perform semantic search on the indexed codebase."""
    queue = state.get("_queue")
    query = state["query"]
    project = state.get("project", "")

    if queue:
        await queue.put({
            "type": "step_start",
            "step": "searching",
            "message": f"Searching codebase: {query[:80]}...",
        })

    results = search_code(query, project_name=project or None, n_results=15)

    if queue:
        await queue.put({
            "type": "step_data",
            "step": "searching",
            "data": {
                "count": len(results),
                "files": list(set(r["file_path"] for r in results))[:8],
            },
        })

    return {
        "search_results": results,
        "current_step": "searching",
    }


async def rerank_node(state: dict) -> dict:
    """Use LLM to rerank and filter search results."""
    queue = state.get("_queue")
    results = state.get("search_results", [])

    if not results:
        return {"reranked_results": [], "current_step": "reranking"}

    if queue:
        await queue.put({
            "type": "step_start",
            "step": "reranking",
            "message": f"Analyzing {len(results)} code snippets for relevance...",
        })

    # Prepare results summary for LLM
    results_summary = []
    for i, r in enumerate(results):
        results_summary.append({
            "index": i,
            "file": r["file_path"],
            "name": r["name"],
            "type": r["chunk_type"],
            "language": r["language"],
            "lines": f"{r['start_line']}-{r['end_line']}",
            "code_preview": r["code"][:300],
            "similarity": r["similarity"],
        })

    provider, api_key = resolve_provider_and_key(state)
    llm = get_llm(provider, api_key)
    prompt = RERANKER_PROMPT.format(
        query=state["query"],
        results=json.dumps(results_summary, ensure_ascii=False, indent=2),
    )

    response = await llm_invoke_with_retry(llm, [HumanMessage(content=prompt)])

    # Parse reranked indices
    try:
        raw = response.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        indices = json.loads(raw)
        reranked = [results[i] for i in indices if 0 <= i < len(results)]
    except (json.JSONDecodeError, IndexError, TypeError):
        # Fallback: take top 5 by similarity
        reranked = results[:5]

    if queue:
        await queue.put({
            "type": "step_data",
            "step": "reranking",
            "data": {
                "selected": len(reranked),
                "files": [r["file_path"] for r in reranked],
            },
        })

    return {
        "reranked_results": reranked,
        "current_step": "reranking",
    }


async def answer_node(state: dict) -> dict:
    """Generate the final answer using LLM with code context."""
    queue = state.get("_queue")
    results = state.get("reranked_results", [])
    history = state.get("conversation_history", [])

    if queue:
        await queue.put({
            "type": "step_start",
            "step": "answering",
            "message": "Generating answer from code context...",
        })

    # Build code context string
    code_parts = []
    for i, r in enumerate(results):
        code_parts.append(
            f"### [{i+1}] {r['file_path']} (L{r['start_line']}-{r['end_line']}) — {r['chunk_type']} `{r['name']}`\n"
            f"```{r['language']}\n{r['code']}\n```\n"
        )
    code_context = "\n".join(code_parts) if code_parts else "No relevant code found."

    provider, api_key = resolve_provider_and_key(state)
    llm = get_llm(provider, api_key, streaming=True)

    # Choose prompt based on conversation history
    if len(history) > 0:
        history_text = "\n".join(
            f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content'][:200]}"
            for h in history[-6:]  # last 3 turns
        )
        prompt = CONVERSATION_PROMPT.format(
            project=state.get("project", "unknown"),
            history=history_text,
            code_context=code_context,
            query=state["query"],
        )
    else:
        prompt = ANSWER_PROMPT.format(
            project=state.get("project", "unknown"),
            query=state["query"],
            code_context=code_context,
        )

    full_answer = ""
    messages = [HumanMessage(content=prompt)]

    for attempt in range(3):
        try:
            async for chunk in llm.astream(messages):
                token = chunk.content
                if token:
                    full_answer += token
                    if queue:
                        await queue.put({"type": "chunk", "content": token})
            break
        except Exception as e:
            error_str = str(e)
            if ("529" in error_str or "429" in error_str) and attempt < 2:
                await asyncio.sleep(5 * (attempt + 1))
                full_answer = ""
            else:
                raise

    # Send done event
    if queue:
        await queue.put({
            "type": "done",
            "data": {
                "answer": full_answer,
                "results": [
                    {
                        "file_path": r["file_path"],
                        "name": r["name"],
                        "chunk_type": r["chunk_type"],
                        "language": r["language"],
                        "start_line": r["start_line"],
                        "end_line": r["end_line"],
                        "similarity": r["similarity"],
                    }
                    for r in results
                ],
                "session_id": state.get("_session_id", ""),
            },
        })

    return {
        "answer": full_answer,
        "current_step": "done",
        "conversation_history": [
            {"role": "user", "content": state["query"]},
            {"role": "assistant", "content": full_answer},
        ],
    }
