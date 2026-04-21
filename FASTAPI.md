# FASTAPI.md — md-bot FastAPI 서비스 문서

## 개요

md-bot의 FastAPI 서비스는 `md_converter` LangGraph 그래프를 HTTP API로 노출합니다.  
클라이언트는 파일을 업로드하거나 서버 경로를 지정하여 문서를 Markdown으로 변환할 수 있습니다.

---

## 파일 구조

```
api/
├── __init__.py
├── main.py      ← FastAPI 앱 생성 및 라우터 등록
├── models.py    ← Pydantic 요청/응답 스키마
└── routes.py    ← 엔드포인트 구현
```

---

## 엔드포인트 목록

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/health` | 서버 상태 확인 |
| `POST` | `/convert/upload` | 파일 업로드 → Markdown 변환 |
| `POST` | `/convert/path` | 서버 경로 지정 → Markdown 변환 |
| `GET` | `/convert/download` | 변환된 `.md` 파일 다운로드 |

---

## 요청/응답 스키마

### `POST /convert/upload`

**요청:** `multipart/form-data`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `file` | binary | ✅ | 변환할 문서 파일 |

---

### `POST /convert/path`

**요청:** `application/json`

```json
{
  "file_path": "/data/documents/report.pdf",
  "output_dir": "/data/output"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `file_path` | string | ✅ | 서버에 존재하는 파일의 절대 경로 |
| `output_dir` | string | ❌ | `.md` 파일 저장 디렉터리 (기본값: 입력 파일 동일 디렉터리) |

---

### 공통 응답 (`ConvertResponse`)

```json
{
  "output_path": "/data/output/report.md",
  "markdown_output": "# Report Title\n\n...",
  "file_format": "pdf"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `output_path` | string | 저장된 `.md` 파일의 절대 경로 |
| `markdown_output` | string | 변환된 Markdown 전체 문자열 |
| `file_format` | string | 감지된 입력 포맷 (`pdf`\|`docx`\|`html`\|`pptx`\|`image`\|`text`) |

---

### `GET /convert/download`

**쿼리 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `output_path` | string | ✅ | `/convert/*` 응답의 `output_path` 값 |

**응답:** `text/markdown` — `.md` 파일 다운로드

---

### `GET /health`

```json
{ "status": "ok" }
```

---

## 서버 실행

### 가상환경 활성화 후 실행 (권장)

```cmd
d:\git\md-bot\.venv\Scripts\activate.bat
uvicorn api.main:app --reload --port 8000 --app-dir "d:\git\md-bot"
```

### 가상환경 직접 경로로 실행

```cmd
d:\git\md-bot\.venv\Scripts\uvicorn.exe api.main:app --reload --port 8000 --app-dir "d:\git\md-bot"
```

### 접속 주소

| 주소 | 설명 |
|------|------|
| `http://localhost:8000/docs` | Swagger UI (대화형 API 테스트) |
| `http://localhost:8000/redoc` | ReDoc 문서 |
| `http://localhost:8000/health` | Health check |

---

## 사용 시퀀스

### 시퀀스 1: 파일 업로드 변환

```
Client                          FastAPI                      md_converter Graph
  │                                │                                │
  │  POST /convert/upload          │                                │
  │  (multipart: file=report.pdf)  │                                │
  │ ──────────────────────────────>│                                │
  │                                │  파일을 임시 디렉터리에 저장   │
  │                                │ ──────────────────────────────>│
  │                                │                                │ FormatDetectorNode
  │                                │                                │   → file_format: "pdf"
  │                                │                                │ PdfExtractorNode
  │                                │                                │   → raw_content
  │                                │                                │ StructureAnalyzerNode (AI)
  │                                │                                │   → structured_content
  │                                │                                │ MarkdownWriterNode
  │                                │                                │   → output_path, markdown_output
  │                                │<──────────────────────────────│
  │  200 OK                        │                                │
  │  { output_path,                │                                │
  │    markdown_output,            │                                │
  │    file_format }               │                                │
  │<──────────────────────────────│                                │
```

### 시퀀스 2: 서버 경로 변환 + 파일 다운로드

```
Client                          FastAPI                      md_converter Graph
  │                                │                                │
  │  POST /convert/path            │                                │
  │  { "file_path": "/data/a.docx"}│                                │
  │ ──────────────────────────────>│                                │
  │                                │  파일 존재 여부 검증           │
  │                                │ ──────────────────────────────>│
  │                                │                                │ FormatDetectorNode → "docx"
  │                                │                                │ DocxExtractorNode → raw_content
  │                                │                                │ StructureAnalyzerNode (AI)
  │                                │                                │ MarkdownWriterNode → a.md 저장
  │                                │<──────────────────────────────│
  │  200 OK { output_path: "/data/a.md", ... }                      │
  │<──────────────────────────────│                                │
  │                                │                                │
  │  GET /convert/download         │                                │
  │  ?output_path=/data/a.md       │                                │
  │ ──────────────────────────────>│                                │
  │                                │  파일 읽기 → FileResponse      │
  │  200 OK (text/markdown)        │                                │
  │  [a.md 파일 다운로드]          │                                │
  │<──────────────────────────────│                                │
```

---

## curl 사용 예시

### 파일 업로드

```bash
curl -X POST http://localhost:8000/convert/upload \
  -F "file=@report.pdf"
```

### 서버 경로 지정

```bash
curl -X POST http://localhost:8000/convert/path \
  -H "Content-Type: application/json" \
  -d "{\"file_path\": \"C:/data/report.pdf\", \"output_dir\": \"C:/data/output\"}"
```

### 변환 결과 파일 다운로드

```bash
curl "http://localhost:8000/convert/download?output_path=C:/data/output/report.md" \
  -o report.md
```

### Health check

```bash
curl http://localhost:8000/health
```

---

## 에러 코드

| HTTP 코드 | 원인 |
|-----------|------|
| `404 Not Found` | `/convert/path`에서 지정한 파일이 서버에 없음 |
| `422 Unprocessable Entity` | 파일명 없음, 경로가 파일이 아님, `.md`가 아닌 경로를 download에 지정 |
| `500 Internal Server Error` | 변환 중 예외 발생 (AI 오류, 라이브러리 오류 등) |

---

## 지원 포맷

| 포맷 | 확장자 | 처리 방식 |
|------|--------|-----------|
| PDF | `.pdf` | `pdfplumber` |
| Word | `.docx`, `.doc` | `python-docx` |
| HTML | `.html`, `.htm` | `BeautifulSoup4` |
| PowerPoint | `.pptx`, `.ppt` | `python-pptx` |
| 이미지 (OCR) | `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp` | `pytesseract` + `Pillow` |
| 텍스트 / CSV | `.txt`, `.csv`, `.tsv`, `.md` | 내장 파일 I/O |
