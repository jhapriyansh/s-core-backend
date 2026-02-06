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

## API Endpoints

### Auth

| Method | Endpoint           | Description                          |
| ------ | ------------------ | ------------------------------------ |
| POST   | `/users`           | Register (username, email, password) |
| POST   | `/users/login`     | Login (email, password) → JWT token  |
| GET    | `/users/{user_id}` | Get user info                        |

### Decks

| Method | Endpoint                           | Description           |
| ------ | ---------------------------------- | --------------------- |
| POST   | `/users/{user_id}/decks`           | Create study deck     |
| GET    | `/users/{user_id}/decks`           | List all decks        |
| GET    | `/users/{user_id}/decks/{deck_id}` | Get deck details      |
| DELETE | `/users/{user_id}/decks/{deck_id}` | Delete deck + vectors |

### Upload & Ingestion

| Method | Endpoint                                            | Description                       |
| ------ | --------------------------------------------------- | --------------------------------- |
| POST   | `/users/{user_id}/decks/{deck_id}/upload`           | Upload files (runs in background) |
| GET    | `/users/{user_id}/decks/{deck_id}/ingestion-status` | Poll processing status            |

### Study

| Method | Endpoint                                          | Description                  |
| ------ | ------------------------------------------------- | ---------------------------- |
| POST   | `/users/{user_id}/decks/{deck_id}/ask`            | Ask a question (RAG)         |
| POST   | `/users/{user_id}/decks/{deck_id}/chat`           | Chat with context history    |
| POST   | `/users/{user_id}/decks/{deck_id}/teach`          | Start/continue teaching mode |
| GET    | `/users/{user_id}/decks/{deck_id}/teach/progress` | Get teaching progress        |
| POST   | `/users/{user_id}/decks/{deck_id}/practice`       | Generate practice questions  |
| GET    | `/users/{user_id}/decks/{deck_id}/coverage`       | Topic coverage analysis      |

---

## File Support

| Format     | Extensions        | Notes                    |
| ---------- | ----------------- | ------------------------ |
| PDF        | .pdf              | Text + embedded images   |
| Word       | .docx             | Text + embedded images   |
| PowerPoint | .pptx             | Text + embedded images   |
| Images     | .png, .jpg, .jpeg | OCR (requires Tesseract) |

---

## Learning Pace System

| Pace   | Theory | Practice | Use Case      |
| ------ | ------ | -------- | ------------- |
| Slow   | 70%    | 30%      | Deep learning |
| Medium | 50%    | 50%      | Balanced      |
| Fast   | 30%    | 70%      | Revision      |

---

## Architecture

```
backend/
├── main.py              # FastAPI app + all endpoints
├── config.py            # Environment & model config
├── auth.py              # JWT + bcrypt authentication
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
│
├── db/
│   ├── chroma.py        # ChromaDB vector storage (per-deck isolation)
│   └── mongo.py         # MongoDB (users, decks, logs)
│
├── ingestion/
│   ├── pipeline.py      # Main ingestion pipeline (background processing)
│   ├── extract.py       # PDF/DOCX/PPTX text extraction
│   ├── chunk.py         # Semantic chunking
│   ├── embed.py         # ONNX Runtime embeddings (all-MiniLM-L6-v2)
│   ├── image_to_text.py # OCR + image description
│   └── syllabus_map.py  # Syllabus topic parsing & filtering
│
└── runtime/
    ├── classify.py      # Intent classification
    ├── retrieve.py      # Semantic retrieval from ChromaDB
    ├── respond.py       # LLM response generation (RAG)
    ├── teach.py         # Teaching mode (structured lessons)
    ├── session.py       # Session & conversation state (in-memory)
    ├── practice.py      # Practice question generation
    ├── coverage.py      # Topic coverage detection
    ├── domain.py        # On-topic / off-topic guard
    ├── internet.py      # DuckDuckGo fallback search
    ├── expand.py        # Query expansion
    └── pace.py          # Learning pace config
```

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
