import json
import asyncio
import uuid
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.config import ALLOWED_ORIGINS
from app.models import IndexRequest, SearchRequest, IndexStatusResponse
from app.indexer.index_manager import (
    index_project, list_projects, delete_project, search_code,
)
from app.agent.graph import run_search_graph

app = FastAPI(title="Code Search Agent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store for conversation history
sessions: dict[str, list[dict]] = {}


@app.get("/")
async def root():
    return {"status": "ok", "service": "Code Search Agent"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/index")
async def index(request: IndexRequest):
    """Index a project directory. Returns indexing stats."""
    try:
        result = index_project(request.path, request.name)
        return result
    except ValueError as e:
        return {"error": str(e), "status": "failed"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.get("/api/projects")
async def projects():
    """List all indexed projects."""
    return {"projects": list_projects()}


@app.delete("/api/projects/{name}")
async def remove_project(name: str):
    """Delete an indexed project."""
    ok = delete_project(name)
    return {"deleted": ok}


@app.post("/api/search")
async def search(request: SearchRequest):
    """Search code with AI agent (SSE streaming)."""
    session_id = request.session_id or str(uuid.uuid4())
    history = sessions.get(session_id, [])

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()

        async def run():
            try:
                await run_search_graph(
                    request.query,
                    request.project or "",
                    session_id,
                    queue,
                    history,
                    provider=request.provider,
                    api_key=request.api_key,
                )
            except Exception as e:
                await queue.put({"type": "error", "content": str(e)})
            finally:
                await queue.put(None)

        task = asyncio.create_task(run())

        while True:
            event = await queue.get()
            if event is None:
                break
            # Save conversation history from done event
            if event.get("type") == "done":
                if session_id not in sessions:
                    sessions[session_id] = []
                sessions[session_id].append({"role": "user", "content": request.query})
                answer = event.get("data", {}).get("answer", "")
                sessions[session_id].append({"role": "assistant", "content": answer})
                # Keep last 10 turns
                sessions[session_id] = sessions[session_id][-20:]

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
