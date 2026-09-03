"""
rag_engine.py
Handles everything that makes this a RAG (Retrieval-Augmented Generation) app:
  1. Extracting text from uploaded files
  2. Splitting text into overlapping chunks
  3. Embedding chunks locally (free, no API needed) with sentence-transformers
  4. Storing/searching those embeddings in a local ChromaDB vector store
  5. Calling the free-tier Gemini API to actually answer / summarize / quiz
"""

import os
import re
import json
import uuid
from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Local, free embedding model (downloads once, then runs offline) ---
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL_NAME)

# --- Persistent local vector store (a folder on disk, no external DB needed) ---
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_store")
client = chromadb.PersistentClient(path=CHROMA_DIR)

COLLECTION_NAME = "study_notes"


def get_collection():
    return client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embed_fn)


def reset_collection():
    """Wipe stored notes so a fresh set of documents can be uploaded."""
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return get_collection()


# ---------- 1. Text extraction ----------

def extract_text(file_path: str, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ---------- 2. Chunking ----------

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# ---------- 3 & 4. Embed + store ----------

def add_document(file_path: str, filename: str) -> int:
    text = extract_text(file_path, filename)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    collection = get_collection()
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)
    return len(chunks)


def retrieve(query: str, n_results: int = 5) -> List[Dict]:
    collection = get_collection()
    if collection.count() == 0:
        return []
    results = collection.query(query_texts=[query], n_results=min(n_results, collection.count()))
    hits = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        hits.append({"text": doc, "source": meta.get("source", "unknown")})
    return hits


def get_all_text(limit_chars: int = 15000) -> str:
    """Pull back stored chunks (used for summarize/quiz, which need broad context)."""
    collection = get_collection()
    if collection.count() == 0:
        return ""
    data = collection.get(limit=collection.count())
    combined = " ".join(data["documents"])
    return combined[:limit_chars]


# ---------- 5. Gemini calls ----------

def _check_key():
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add your free key from https://aistudio.google.com/app/apikey"
        )


def answer_question(question: str) -> Dict:
    _check_key()
    hits = retrieve(question, n_results=5)
    if not hits:
        return {
            "answer": "I don't have any notes uploaded yet, so I can't answer from your material. Upload a document first.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    prompt = f"""You are a careful study assistant. Answer the question using ONLY the context below,
which comes from the student's own notes. If the context doesn't contain the answer, say so honestly
instead of guessing. Be clear and concise, and explain like a helpful tutor.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    sources = sorted(set(h["source"] for h in hits))
    return {"answer": response.text.strip(), "sources": sources}


def summarize_notes() -> str:
    _check_key()
    text = get_all_text()
    if not text:
        return "No notes uploaded yet. Upload a document first."

    prompt = f"""Summarize the following study material into clear, well-organized notes.
Use short headings and bullet points. Focus on the key concepts a student needs to remember for an exam.

MATERIAL:
{text}

SUMMARY:"""
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    return response.text.strip()


def generate_quiz(num_questions: int = 5) -> List[Dict]:
    _check_key()
    text = get_all_text()
    if not text:
        return []

    prompt = f"""Based on the study material below, create exactly {num_questions} multiple-choice
questions to help a student revise. Return ONLY valid JSON, no markdown fences, no extra text,
in exactly this shape:

[
  {{
    "question": "...",
    "options": {{"a": "...", "b": "...", "c": "...", "d": "..."}},
    "correct": "a",
    "explanation": "..."
  }}
]

MATERIAL:
{text}"""
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []
