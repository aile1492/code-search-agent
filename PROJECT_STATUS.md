# Code Search Agent - Project Status

## Overview
AI-powered codebase search tool. Tree-sitter로 코드를 AST 파싱하고, 벡터 임베딩으로 시맨틱 검색 후, Claude가 답변을 생성하는 LangGraph 기반 에이전트.

---

## Completed (완료)

### Backend (Python FastAPI + LangGraph)

| 파일 | 설명 | 상태 |
|------|------|------|
| `app/main.py` | FastAPI 서버 (인덱싱 + 검색 SSE + 프로젝트 관리 API) | Done |
| `app/config.py` | 환경변수 (ANTHROPIC_API_KEY, CHROMA_PERSIST_DIR) | Done |
| `app/models.py` | Pydantic 스키마 (IndexRequest, SearchRequest) | Done |
| `app/agent/state.py` | LangGraph 상태 스키마 (SearchState) | Done |
| `app/agent/graph.py` | LangGraph 그래프: search → rerank → answer | Done |
| `app/agent/nodes.py` | 3개 노드 (search_node, rerank_node, answer_node) | Done |
| `app/agent/prompts.py` | LLM 시스템 프롬프트 (reranker, answer, conversation) | Done |
| `app/indexer/chunker.py` | Tree-sitter AST 파싱, 7개 언어 지원 | Done |
| `app/indexer/embedder.py` | all-MiniLM-L6-v2 임베딩 모델 래퍼 | Done |
| `app/indexer/index_manager.py` | ChromaDB 벡터 DB 관리 (인덱싱/검색/삭제) | Done |
| `requirements.txt` | 의존성 목록 | Done |
| `.env` | API 키, CORS 설정 | Done |
| `venv/` | Python 가상환경, 패키지 설치 완료 | Done |

### Frontend (Next.js 16 + Tailwind CSS)

| 파일 | 설명 | 상태 |
|------|------|------|
| `src/components/SearchWindow.tsx` | 메인 레이아웃 (헤더, 패널 분할, 상태 관리) | Done |
| `src/components/ProjectSelector.tsx` | 프로젝트 선택 드롭다운 + 인덱싱 UI | Done |
| `src/components/SearchInput.tsx` | 검색 입력 (일반 + compact 모드) | Done |
| `src/components/StepTimeline.tsx` | 에이전트 단계 타임라인 (searching → reranking → answering) | Done |
| `src/components/AnswerView.tsx` | 마크다운 답변 렌더링 + 코드 하이라이팅 + 참조 코드 목록 | Done |
| `src/hooks/useSearch.ts` | SSE 이벤트 → React 상태 관리 훅 | Done |
| `src/lib/api.ts` | API 클라이언트 (wakeServer, getProjects, indexProject, startSearch) | Done |
| `src/lib/types.ts` | TypeScript 타입 (SSEEvent, CodeResult, Project, AgentStep) | Done |
| `src/app/page.tsx` | 메인 페이지 (SearchWindow 렌더) | Done |
| `src/app/layout.tsx` | 레이아웃 (메타데이터, 폰트) | Done |
| `src/app/globals.css` | 글로벌 스타일 (typography, scrollbar, 애니메이션) | Done |

### Multi-Provider LLM Support (멀티 프로바이더)

| 파일 | 설명 | 상태 |
|------|------|------|
| `app/config.py` | Gemini/Groq 키 + DEFAULT_PROVIDER 설정 추가 | Done |
| `app/models.py` | SearchRequest에 provider/api_key 필드 추가 | Done |
| `app/agent/state.py` | SearchState에 _provider/_api_key 추가 | Done |
| `app/agent/nodes.py` | get_llm() 멀티 provider 지원 (Gemini/Anthropic/Groq) | Done |
| `app/agent/graph.py` | run_search_graph()에 provider/api_key 파라미터 추가 | Done |
| `app/main.py` | 검색 요청에서 provider/api_key를 graph로 전달 | Done |
| `src/lib/types.ts` | LLMProvider, LLMSettings 타입 추가 | Done |
| `src/lib/api.ts` | startSearch()에 LLMSettings 전달 지원 | Done |
| `src/hooks/useSearch.ts` | search()에 LLMSettings 파라미터 추가 | Done |
| `src/components/LLMSettingsPanel.tsx` | Provider 선택 + API 키 입력 UI (localStorage 저장) | Done |
| `src/components/SearchWindow.tsx` | 헤더에 LLMSettingsPanel 통합 | Done |
| `requirements.txt` | langchain-google-genai, langchain-groq 추가 | Done |

**지원 Provider:**
| Provider | 모델 | 비용 |
|----------|------|------|
| Google Gemini (기본) | Gemini 2.0 Flash | 무료 |
| Anthropic | Claude Sonnet 4 | 유료 |
| Groq | Llama 3.3 70B | 무료 (속도 제한) |

**동작 방식:**
- 기본: 서버의 Gemini 무료 키로 동작 (방문자 즉시 체험)
- 유저가 자기 API 키를 입력하면 해당 키로 전환
- API 키는 브라우저 localStorage에만 저장, 서버에 저장하지 않음

### Tests Passed (검증 완료)

- [x] Tree-sitter 파싱: Research Agent 프로젝트 22파일 → 56 코드 청크 추출 성공
- [x] ChromaDB 인덱싱: 56 청크 → 벡터 DB 저장 성공
- [x] 시맨틱 검색: "SSE streaming endpoint" → main.py의 research 엔드포인트 정확히 찾음
- [x] 백엔드 서버: `http://localhost:8002/health` → `{"status":"ok"}`
- [x] 프로젝트 API: `GET /api/projects` → 인덱싱된 프로젝트 목록 반환
- [x] 프론트엔드 빌드: `npx next build` → Compiled successfully

### Supported Languages (지원 언어)

Python (.py), JavaScript (.js/.jsx), TypeScript (.ts/.tsx), Java (.java), C++ (.cpp/.cc/.h/.hpp), Go (.go), Rust (.rs)

---

## Known Issues (알려진 문제)

### 1. 메모리 과다 사용 (Critical)

**증상**: 프론트엔드(`npm run dev`) + 백엔드 서버 동시 실행 시 시스템 메모리 부족

**원인**:
- `sentence-transformers` 패키지가 **PyTorch (~800MB)**를 의존성으로 설치
- 백엔드 서버 기동 시 임베딩 모델 로드 → RAM 추가 사용
- 프론트엔드 dev 서버 (Turbopack) + 백엔드 동시 실행 = 2GB+ 메모리 필요

**해결 방안** (우선순위 순):
1. **PyTorch CPU-only 경량 버전**: `torch` 대신 `torch --index-url https://download.pytorch.org/whl/cpu` 사용 (800MB → ~200MB)
2. **ONNX Runtime으로 교체**: `sentence-transformers` 대신 `onnxruntime` + `optimum` 사용하면 PyTorch 불필요 (가장 작은 풋프린트)
3. **임베딩 모델 lazy loading**: 서버 시작 시 로드하지 않고, 첫 검색 시에만 로드
4. **프론트엔드**: `.next/` 캐시 삭제 후 재시작

---

## TODO (남은 작업)

### Phase 1: 메모리 문제 해결 (필수)
- [ ] PyTorch CPU-only로 교체 또는 ONNX Runtime 방식으로 전환
- [ ] 임베딩 모델 lazy loading 적용
- [ ] 메모리 사용량 측정 (before/after)

### Phase 2: E2E 통합 테스트 (필수)
- [ ] 백엔드 + 프론트엔드 동시 기동
- [ ] UI에서 프로젝트 인덱싱 테스트
- [ ] UI에서 코드 검색 → 답변 스트리밍 테스트
- [ ] follow-up 질문 (대화 컨텍스트) 테스트
- [ ] 에러 핸들링 테스트 (잘못된 경로, 빈 프로젝트 등)

### Phase 3: Git + GitHub (필수)
- [ ] `git init` + 초기 커밋
- [ ] GitHub 레포 생성 (`aile1492/code-search-agent`)
- [ ] push

### Phase 4: 배포 (선택)
- [ ] Render 백엔드 배포 (메모리 제한 주의 — 무료 플랜 512MB)
- [ ] Vercel 프론트엔드 배포
- [ ] UptimeRobot 등록

### Phase 5: 포트폴리오 (선택)
- [ ] Notion 서브페이지 생성
- [ ] 메인 포트폴리오에 항목 추가
- [ ] README.md 작성

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, react-markdown, rehype-highlight |
| Backend | Python 3.12, FastAPI, Uvicorn |
| AI Orchestration | LangGraph (StateGraph) |
| LLM | Gemini 2.0 Flash (기본) / Claude Sonnet 4 / Llama 3.3 70B (선택) |
| Code Parsing | Tree-sitter (7 languages) |
| Embedding | all-MiniLM-L6-v2 (sentence-transformers) |
| Vector DB | ChromaDB (persistent, local) |
| Streaming | SSE (Server-Sent Events) + asyncio.Queue |

## Architecture

```
User Question (자연어)
     ↓
[search_node] ChromaDB 벡터 검색 (15 results)
     ↓
[rerank_node] Claude가 관련성 순으로 재정렬 (top 5)
     ↓
[answer_node] Claude가 코드 컨텍스트 기반 답변 생성 (SSE 스트리밍)
     ↓
Frontend에 실시간 표시
```

## Ports

| Service | Port |
|---------|------|
| Backend | 8002 |
| Frontend | 3002 |

## Commands

```bash
# Backend
cd backend
venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Frontend
cd frontend
npm run dev -- -p 3002

# Index a project
curl -X POST http://localhost:8002/api/index -H "Content-Type: application/json" -d "{\"path\": \"C:\\\\path\\\\to\\\\project\", \"name\": \"my-project\"}"
```
