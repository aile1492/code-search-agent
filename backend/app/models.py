from pydantic import BaseModel


class IndexRequest(BaseModel):
    path: str  # directory path to index
    name: str | None = None  # optional project name


class SearchRequest(BaseModel):
    query: str
    project: str | None = None  # optional: search specific project
    session_id: str | None = None
    provider: str | None = None  # "gemini" | "anthropic" | "groq"
    api_key: str | None = None  # user-provided API key


class IndexStatusResponse(BaseModel):
    project: str
    total_files: int
    total_chunks: int
    languages: list[str]
    status: str
