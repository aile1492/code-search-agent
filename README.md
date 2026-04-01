# Code Search Agent

AI-powered codebase search tool that understands your code semantically. Ask natural language questions about any codebase and get accurate, context-aware answers backed by relevant code snippets.

## Features

- **Semantic Code Search** - Vector embeddings find conceptually related code, not just keyword matches
- **Multi-Language Support** - Python, JavaScript, TypeScript, Java, C++, Go, Rust
- **AST-Aware Chunking** - Tree-sitter parses code into meaningful units (functions, classes, methods)
- **LLM-Powered Reranking** - AI filters and ranks results by relevance before generating answers
- **Real-Time Streaming** - Server-Sent Events deliver answers token by token
- **Multi-Provider LLM** - Choose between Groq (free), Anthropic Claude, or Google Gemini
- **Conversation Memory** - Follow-up questions maintain context from previous exchanges

## Architecture

```
User Question (natural language)
       |
[search_node] ChromaDB vector search (15 results)
       |
[rerank_node] LLM reranks by relevance (top 5)
       |
[answer_node] LLM generates answer with code context (SSE streaming)
       |
Frontend renders in real-time
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, Uvicorn |
| AI Orchestration | LangGraph (StateGraph) |
| LLM | Groq Llama 3.3 70B (default) / Claude Sonnet 4 / Gemini 2.0 Flash |
| Code Parsing | Tree-sitter (7 languages) |
| Embedding | all-MiniLM-L6-v2 (sentence-transformers) |
| Vector DB | ChromaDB (persistent, local) |
| Streaming | SSE (Server-Sent Events) + asyncio.Queue |

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key        # optional
ANTHROPIC_API_KEY=your_anthropic_api_key  # optional
DEFAULT_PROVIDER=groq
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3002
CHROMA_PERSIST_DIR=./chroma_db
```

Start the server:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev -- -p 3002
```

Open http://localhost:3002

### Index a Project

```bash
curl -X POST http://localhost:8002/api/index \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/your/project", "name": "my-project"}'
```

Or use the UI to index projects directly.

## LLM Provider Options

| Provider | Model | Cost | How to Get Key |
|----------|-------|------|----------------|
| **Groq** (default) | Llama 3.3 70B | Free | [console.groq.com](https://console.groq.com) |
| Google Gemini | Gemini 2.0 Flash | Free | [aistudio.google.com](https://aistudio.google.com/apikey) |
| Anthropic | Claude Sonnet 4 | Paid | [console.anthropic.com](https://console.anthropic.com) |

The app works out of the box with the server's default Groq key. Users can optionally enter their own API key in the settings panel to use a different provider.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/index` | Index a project directory |
| GET | `/api/projects` | List indexed projects |
| DELETE | `/api/projects/{name}` | Delete a project |
| POST | `/api/search` | Search with AI agent (SSE stream) |

## License

MIT
