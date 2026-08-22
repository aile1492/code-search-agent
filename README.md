# Code Search Agent

개발자가 자연어로 질문하면 큰 코드 프로젝트에서 관련 파일과 함수를 찾아 코드 근거와 함께 답변하는 검색 도구입니다.

단순한 단어 검색에 그치지 않고 코드의 구조와 의미를 함께 분석합니다. 검색된 코드 중 질문과 관련성이 높은 부분을 AI가 다시 비교하고, 선택된 코드를 근거로 답변합니다.

## 주요 기능

- **의미 기반 코드 검색**: 이름이 달라도 역할이 비슷한 코드를 찾습니다.
- **여러 언어 지원**: Python, JavaScript, TypeScript, Java, C++, Go, Rust
- **코드 구조 분석**: Tree-sitter로 함수, 클래스, 메서드 단위로 코드를 나눕니다.
- **검색 결과 재검토**: AI가 검색 결과의 관련성을 비교해 답변에 사용할 코드를 선택합니다.
- **실시간 답변 표시**: 생성 중인 답변을 화면에 순서대로 전달합니다.
- **여러 AI 모델 지원**: Groq, Anthropic Claude, Google Gemini 중 선택할 수 있습니다.
- **대화 맥락 유지**: 후속 질문에서도 앞선 질문과 답변의 맥락을 이어갑니다.

## 동작 과정

```text
사용자 질문
   |
[search_node] ChromaDB에서 관련 코드 15개 검색
   |
[rerank_node] AI가 관련성을 비교해 상위 5개 선택
   |
[answer_node] 선택된 코드를 근거로 답변 생성
   |
화면에 답변을 실시간으로 표시
```

## 사용 기술

| 영역 | 기술 |
|---|---|
| 화면 | Next.js 16, React 19, TypeScript, Tailwind CSS |
| 서버 | Python 3.12, FastAPI, Uvicorn |
| AI 작업 흐름 | LangGraph |
| AI 모델 | Groq, Claude, Gemini |
| 코드 분석 | Tree-sitter |
| 의미 변환 | sentence-transformers |
| 검색 저장소 | ChromaDB |
| 실시간 전달 | SSE, asyncio.Queue |

## 실행 방법

### 준비 사항

- Python 3.12 이상
- Node.js 18 이상
- 사용할 AI 서비스의 API 키

### 서버 실행

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`backend/.env` 파일을 만듭니다.

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DEFAULT_PROVIDER=groq
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3002
CHROMA_PERSIST_DIR=./chroma_db
```

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### 화면 실행

```bash
cd frontend
npm install
npm run dev -- -p 3002
```

브라우저에서 `http://localhost:3002`를 엽니다.

### 코드 프로젝트 등록

```bash
curl -X POST http://localhost:8002/api/index \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/your/project", "name": "my-project"}'
```

화면에서도 프로젝트 경로와 이름을 입력해 등록할 수 있습니다.

## API

| 방식 | 주소 | 역할 |
|---|---|---|
| GET | `/health` | 서버 상태 확인 |
| POST | `/api/index` | 코드 프로젝트 분석과 등록 |
| GET | `/api/projects` | 등록된 프로젝트 목록 확인 |
| DELETE | `/api/projects/{name}` | 등록된 프로젝트 삭제 |
| POST | `/api/search` | AI 코드 검색 시작 |
| POST | `/api/search/raw` | LLM 없이 의미 검색 결과와 코드 위치 반환 |

`/api/search/raw`는 다른 개발 도구가 Code Search Agent를 검색 Tool로 재사용할 때 사용합니다. 답변 생성과 API Key 없이 ChromaDB 검색 결과만 JSON으로 반환합니다.

## 라이선스

MIT
