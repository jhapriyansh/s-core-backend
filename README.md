# S-Core Backend

**Syllabus-Aware AI Study Companion**

S-Core is a knowledge alignment engine that enforces syllabus boundaries, diagnoses missing knowledge, adapts learning depth, and generates theory + practice content.

## What S-Core Is

- ✅ A disciplined cognitive learning system
- ✅ Memory, scope control, adaptive reasoning
- ✅ Trust boundaries enforced

## What S-Core Is NOT

- ❌ Not a chatbot
- ❌ Not a PDF Q&A tool
- ❌ Not a search engine

---

## Quick Start

### 1. Setup Virtual Environment

```bash
cd backend
python -m venv venv
source ./venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate     # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract (for OCR)

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows - download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### 4. Setup MongoDB

```bash
# macOS
brew install mongodb-community
brew services start mongodb-community

# Or use Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 5. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 6. Run Server

```bash
uvicorn main:app --reload --port 8000
```

Visit: http://localhost:8000/docs for API documentation

---

## Core Philosophy (System Invariants)

These are non-negotiable system laws:

1. **Syllabus is ground truth** - No content survives unless it maps to syllabus
2. **No hallucination beyond scope** - Only use uploaded material
3. **Every deck is isolated** - No cross-deck contamination
4. **Images become text** - No raw images stored
5. **Internet is a patch, not memory** - External info never stored
6. **System knows when knowledge is missing** - Explicit coverage detection

---

## API Endpoints

### Users

- `POST /users` - Create user
- `GET /users/{user_id}` - Get user info

### Decks

- `POST /users/{user_id}/decks` - Create study deck
- `GET /users/{user_id}/decks` - List all decks
- `GET /users/{user_id}/decks/{deck_id}` - Get deck info
- `DELETE /users/{user_id}/decks/{deck_id}` - Delete deck

### Upload & Ingestion

- `POST /users/{user_id}/decks/{deck_id}/upload` - Upload files

### Query

- `POST /users/{user_id}/decks/{deck_id}/ask` - Ask question
- `POST /users/{user_id}/decks/{deck_id}/practice` - Generate practice

### Coverage

- `GET /users/{user_id}/decks/{deck_id}/coverage` - Topic coverage analysis

---

## File Support

| Format     | Extension         | Notes                   |
| ---------- | ----------------- | ----------------------- |
| PDF        | .pdf              | Text + images extracted |
| Word       | .docx, .doc       | Text + images extracted |
| PowerPoint | .pptx, .ppt       | Text + images extracted |
| Plain Text | .txt, .md         | Direct text             |
| Images     | .png, .jpg, .jpeg | OCR + LLM description   |

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
├── main.py              # FastAPI application
├── config.py            # Configuration
├── requirements.txt     # Dependencies
│
├── db/
│   ├── chroma.py        # Vector storage (ChromaDB)
│   └── mongo.py         # Document storage (MongoDB)
│
├── ingestion/
│   ├── pipeline.py      # Main ingestion pipeline
│   ├── extract.py       # File extraction
│   ├── chunk.py         # Semantic chunking
│   ├── image_to_text.py # Image processing
│   ├── syllabus_map.py  # Syllabus filtering
│   └── embed.py         # Text embeddings
│
└── runtime/
    ├── classify.py      # Intent classification
    ├── retrieve.py      # Semantic retrieval
    ├── respond.py       # Response generation
    ├── coverage.py      # Coverage detection
    ├── domain.py        # Scope checking
    ├── internet.py      # Internet enhancement
    ├── expand.py        # Topic expansion
    ├── pace.py          # Pace configuration
    └── practice.py      # Question generation
```

---

## Practice Question Types

1. **Conceptual** - Definitions, explanations, comparisons
2. **Application** - Scenario analysis, tracing, classification
3. **Numerical** - Calculations, algorithms, formulas

Each question includes:

- The question
- Final answer
- Step-by-step solution

---

## Internet Enhancement

Triggered when:

- Local similarity score is low
- Prerequisite missing
- Topic outside syllabus

Whitelisted domains:

- wikipedia.org
- geeksforgeeks.org
- tutorialspoint.com

Rules:

- Never stored
- Never embedded
- Always labeled `[Internet Enhanced]`

---

## Tech Stack

- **Framework**: FastAPI
- **LLM**: Groq (llama-3.3-70b-versatile)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector DB**: ChromaDB
- **Document DB**: MongoDB
- **OCR**: Tesseract

---

## License

MIT
