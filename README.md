# 📚 Study Agent — AI-Powered Study Assistant

An AI study assistant that lets you upload PDF or text documents, ask questions about them, and auto-generate quizzes to test your understanding — all powered by RAG (Retrieval-Augmented Generation).

> Built with FastAPI · Streamlit · Groq (LLaMA 3.3 70B) · Sentence Transformers

---

## Features

- **Document Q&A** — Upload any PDF or `.txt` file and ask questions in natural language. Answers are grounded in your document and supplemented by the LLM's own knowledge.
- **Conversation Memory** — Follow-up questions work naturally; the assistant remembers the last 3 exchanges.
- **Multi-document Support** — Upload multiple documents and switch between them using the document selector. Queries stay scoped to the selected document.
- **Quiz Generator** — Auto-generate 3–10 multiple choice questions from any uploaded document. Instant scoring with explanations after submission.
- **Persistent Storage** — Uploaded documents are indexed and saved to disk — they survive server restarts.

---

## How It Works

```
PDF / TXT
   │
   ▼
[Chunker] — splits text into 1000-char overlapping chunks
   │
   ▼
[Embedder] — converts each chunk to a vector (all-MiniLM-L6-v2, runs locally)
   │
   ▼
[Vector Store] — saves chunks + embeddings to disk (JSON)
   │
   ▼  (on query)
[Retriever] — embeds the question, finds top-5 most similar chunks via cosine similarity
   │
   ▼
[LLM] — Groq LLaMA 3.3 70B generates the answer using retrieved chunks as context
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| LLM | Groq API (LLaMA 3.3 70B Versatile) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, no API needed) |
| PDF Parsing | pypdf |
| Vector Storage | JSON file (persistent, no external DB) |

---

## Project Structure

```
study-agent/
├── backend/
│   ├── app.py          # FastAPI app, CORS, router
│   ├── llm.py          # Groq client, multi-turn chat
│   ├── embeddings.py   # Local sentence-transformer model
│   ├── vector_db.py    # Persistent vector store (JSON)
│   ├── chunker.py      # Text splitting with overlap
│   └── routes/
│       └── api.py      # All API endpoints
├── frontend/
│   └── app.py          # Streamlit chat + quiz UI
├── requirements.txt
└── .env                # GROQ_API_KEY goes here
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/study-agent.git
cd study-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key

Create a `.env` file in the `study-agent/` directory:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com).

---

## Running Locally

Open **two terminals** inside the `study-agent/` folder.

**Terminal 1 — Backend:**
```bash
venv\Scripts\activate
uvicorn backend.app:app --reload
```

**Terminal 2 — Frontend:**
```bash
venv\Scripts\activate
streamlit run frontend/app.py
```

Then open **http://localhost:8501** in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/ping` | Health check |
| `GET` | `/api/documents` | List all indexed documents |
| `POST` | `/api/upload` | Upload and index a PDF or TXT file |
| `POST` | `/api/query` | Ask a question (RAG pipeline) |
| `POST` | `/api/quiz` | Generate MCQ quiz from a document |

### Example — Query

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is photosynthesis?", "doc_filter": "biology_notes.pdf"}'
```

### Example — Quiz

```bash
curl -X POST http://localhost:8000/api/quiz \
  -H "Content-Type: application/json" \
  -d '{"doc_filter": "biology_notes.pdf", "num_questions": 5}'
```

---

## Usage

1. **Upload a document** — Use the sidebar to upload a PDF or TXT file and click "Upload & Index"
2. **Select the document** — Pick it from the "Active Document" dropdown to restrict search to that file
3. **Chat** — Type questions in the Chat tab; the assistant answers from your document
4. **Quiz** — Switch to the Quiz tab, set the number of questions, and click "Generate Quiz"
5. **Score** — Submit your answers to see which were correct with explanations

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (required) |
