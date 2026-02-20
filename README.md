# S-Core Backend

**Syllabus-Aware AI Study Companion**

S-Core is a knowledge alignment engine that enforces syllabus boundaries, diagnoses missing knowledge, adapts learning depth, and generates theory + practice content.

## What S-Core Is

- ✅ A disciplined cognitive learning system
- ✅ Memory, scope control, adaptive reasoning
- ✅ Trust boundaries enforced

---

## Prerequisites

- **Python 3.10+**
- **MongoDB** (local or remote)
- **Groq API key** — free at [console.groq.com](https://console.groq.com)
- **Tesseract** (optional — only needed for scanned image OCR)
- **Frontend** (optional but recommended) — see [frontend README](https://github.com/jhapriyansh/s-core-frontend) for setup

---

## Setup

### 1. Clone & Enter

```bash
cd s-core/backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
# or
.\venv\Scripts\activate    # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> First run will also download the ONNX embedding model (~90MB) to `~/.cache/score_models/`. This is a one-time download.

### 4. Start MongoDB

```bash
# macOS (Homebrew)
brew install mongodb-community
brew services start mongodb-community
```

### 5. Run the Server

```bash
uvicorn main:app --reload --port 8000
```

The API is now live at **http://localhost:8000**. Docs at **http://localhost:8000/docs**.

---

## Tech Stack

| Component   | Technology                                 |
| ----------- | ------------------------------------------ |
| Framework   | FastAPI                                    |
| LLM         | Groq — Llama 3.3 70B                       |
| Embeddings  | ONNX Runtime — all-MiniLM-L6-v2 (384 dims) |
| Vector DB   | ChromaDB (persistent, per-deck isolation)  |
| Document DB | MongoDB                                    |
| Auth        | JWT (PyJWT) + bcrypt                       |
| Doc Parsing | pdfplumber, python-docx, python-pptx       |
| OCR         | Tesseract (optional)                       |
| Internet    | DuckDuckGo search (fallback only)          |

---

## Known Limitations

- **Chat sessions are in-memory** — lost on server restart. Decks, users, and vectors persist fine.
- **Tesseract required for scanned images** — if not installed, image uploads will fail. Text-based PDFs/PPTX/DOCX work without it.
- **Groq rate limits** — free tier allows ~30 requests/minute.

---

## License

MIT
