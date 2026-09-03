# Study Assistant — AI-Powered Notes Q&A, Summarizer & Quiz Generator

A retrieval-augmented (RAG) study tool: upload your lecture notes or textbook PDFs,
then ask questions, generate exam-ready summaries, and auto-generate multiple-choice
quizzes — all answered strictly from *your own material*, not generic internet answers.

Built to be genuinely useful during exam revision, and to demonstrate applied RAG /
LLM-integration skills end-to-end: document ingestion, chunking, local embeddings,
vector search, and grounded generation.

## How it works

1. **Ingest** — PDFs/text files are parsed and split into overlapping chunks.
2. **Embed** — each chunk is converted into a vector locally using
   `sentence-transformers` (no API cost, runs on CPU).
3. **Store & retrieve** — vectors are stored in a local **ChromaDB** database; a
   question is embedded the same way and matched against the closest chunks.
4. **Generate** — the retrieved chunks are passed as context to **Gemini's free-tier
   API**, which answers, summarizes, or writes quiz questions grounded in that context.

This is the same core pattern (RAG) used in production AI products — the project
just applies it to a study-notes use case.

## Tech stack

| Layer            | Technology                                   |
|-------------------|-----------------------------------------------|
| Backend API       | FastAPI (Python)                              |
| Embeddings        | sentence-transformers (`all-MiniLM-L6-v2`)    |
| Vector store      | ChromaDB (local, persistent)                  |
| LLM               | Google Gemini API (free tier)                 |
| PDF parsing       | pypdf                                         |
| Frontend          | Vanilla HTML/CSS/JS (no build step required)  |

Everything here is free — no paid API keys, no paid hosting required to run locally.

## Features

- Upload multiple PDF / `.txt` files at once
- Ask natural-language questions, answered only from your uploaded notes
- Answers cite which document they came from
- One-click chapter/topic summarization into structured notes
- Auto-generated multiple-choice quiz with instant feedback and explanations
- Clear/reset your notes at any time

## Setup

### 1. Clone and install backend dependencies

```bash
git clone <your-repo-url>
cd study-assistant/backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add your free Gemini API key

Get a free key (no credit card needed) at
[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

```bash
cp .env.example .env
# then edit .env and paste your key in GEMINI_API_KEY
```

### 3. Run it

```bash
python main.py
```

Open **http://localhost:8000** in your browser. Upload a PDF, and start asking questions.

## Project structure

```
study-assistant/
├── backend/
│   ├── main.py           # FastAPI routes
│   ├── rag_engine.py     # chunking, embeddings, vector store, Gemini calls
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── index.html        # UI (vanilla JS, no build tooling needed)
└── README.md
```

## Possible extensions

- Flashcard mode (spaced repetition)
- Per-document filtering in the Ask tab
- Support for `.docx` / `.pptx` slide uploads
- Swap Gemini for a fully local model (Ollama) for zero-API-key usage
- Deploy free on Render / Hugging Face Spaces for a live demo link

## Why this project

Built as a portfolio project to demonstrate applied RAG and LLM-integration skills —
the same underlying pattern used in real-world AI products — while solving a genuine,
personal problem: revising efficiently from your own notes.
