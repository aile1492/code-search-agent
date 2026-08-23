from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    path: str  # directory path to index
    name: str | None = None  # optional project name


class SearchRequest(BaseModel):
    query: str
    project: str | None = None  # optional: search specific project
    session_id: str | None = None
    provider: str | None = None  # "gemini" | "anthropic" | "groq"
    api_key: str | None = None  # user-provided API key


class RawSearchRequest(BaseModel):
    query: str
    project: str | None = None
    n_results: int = Field(default=10, ge=1, le=25)


class IndexStatusResponse(BaseModel):
    project: str
    total_files: int
    total_chunks: int
    languages: list[str]
    status: str
