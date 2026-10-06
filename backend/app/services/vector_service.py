import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import httpx
from app.config import DATA_DIR, settings

DOCS_META_FILE = DATA_DIR / "documents_meta.json"
STATS_FILE = DATA_DIR / "stats.json"
CHUNKS_FILE = DATA_DIR / "chunks.json"


# ---------------------------------------------------------------------------
# Lightweight pure-Python vector store (TF-IDF cosine similarity)
# Replaces chromadb to avoid C++ build failures on Render free tier
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tfidf_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    tf = Counter(tokens)
    total = len(tokens) or 1
    return {t: (count / total) * idf.get(t, 1.0) for t, count in tf.items()}


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    dot = sum(a.get(t, 0.0) * b.get(t, 0.0) for t in b)
    mag_a = math.sqrt(sum(v * v for v in a.values())) or 1.0
    mag_b = math.sqrt(sum(v * v for v in b.values())) or 1.0
    return dot / (mag_a * mag_b)


class SimpleVectorStore:
    """
    File-backed TF-IDF vector store.
    Stores chunks as a list in chunks.json on disk.
    """

    def __init__(self, chunks_file: Path):
        self.chunks_file = chunks_file
        self._chunks: list[dict[str, Any]] = []
        self._idf: dict[str, float] = {}
        self._load()

    def _load(self):
        if self.chunks_file.exists():
            try:
                with open(self.chunks_file, encoding="utf-8") as f:
                    self._chunks = json.load(f)
                self._rebuild_idf()
            except Exception:
                self._chunks = []

    def _save(self):
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            json.dump(self._chunks, f)

    def _rebuild_idf(self):
        df: Counter = Counter()
        N = len(self._chunks) or 1
        for chunk in self._chunks:
            tokens = set(_tokenize(chunk.get("text", "")))
            for t in tokens:
                df[t] += 1
        self._idf = {t: math.log(N / (1 + cnt)) + 1.0 for t, cnt in df.items()}

    def add(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> None:
        existing_ids = {c["id"] for c in self._chunks}
        for chunk_id, text, meta in zip(ids, documents, metadatas, strict=False):
            if chunk_id not in existing_ids:
                self._chunks.append({"id": chunk_id, "text": text, "meta": meta})
        self._rebuild_idf()
        self._save()

    def delete(self, document_id: str) -> None:
        self._chunks = [
            c for c in self._chunks if c.get("meta", {}).get("document_id") != document_id
        ]
        self._rebuild_idf()
        self._save()

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        document_id: str | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> list[dict[str, Any]]:
        candidates = self._chunks

        # Filter by ownership
        if document_id:
            candidates = [
                c for c in candidates if c.get("meta", {}).get("document_id") == document_id
            ]
        elif user_id and not is_admin:
            candidates = [c for c in candidates if c.get("meta", {}).get("user_id") == user_id]

        if not candidates:
            return []

        q_tokens = _tokenize(query_text)
        q_vec = _tfidf_vector(q_tokens, self._idf)

        scored = []
        for chunk in candidates:
            c_tokens = _tokenize(chunk.get("text", ""))
            c_vec = _tfidf_vector(c_tokens, self._idf)
            sim = _cosine_similarity(q_vec, c_vec)
            scored.append((sim, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "text": c["text"],
                "similarity": round(sim, 4),
                "meta": c.get("meta", {}),
            }
            for sim, c in scored[:n_results]
        ]

    def get_chunks_for_doc(self, document_id: str) -> list[dict]:
        return sorted(
            [c for c in self._chunks if c.get("meta", {}).get("document_id") == document_id],
            key=lambda c: c.get("meta", {}).get("chunk_index", 0),
        )

    def count(self) -> int:
        return len(self._chunks)


# ---------------------------------------------------------------------------
# VectorService — same public API as before, now backed by SimpleVectorStore
# ---------------------------------------------------------------------------


class VectorService:
    def __init__(self, data_dir: Path | None = None, chroma_dir: Path | None = None):
        self.data_dir = data_dir or DATA_DIR
        # chroma_dir kept for signature compatibility; not used
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.docs_meta_file = self.data_dir / "documents_meta.json"
        self.stats_file = self.data_dir / "stats.json"
        self.chunks_file = self.data_dir / "chunks.json"
        self._init_storage()
        self.store = SimpleVectorStore(self.chunks_file)
        self._migrate_existing_docs()

    def _init_storage(self):
        if not self.docs_meta_file.exists():
            with open(self.docs_meta_file, "w", encoding="utf-8") as f:
                json.dump({}, f)
        if not self.stats_file.exists():
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "global": {
                            "tests_taken": 0,
                            "total_score_sum": 0,
                            "total_questions_answered": 0,
                            "topics_revised": 0,
                        },
                        "users": {},
                    },
                    f,
                )

    def _migrate_existing_docs(self):
        try:
            with open(self.docs_meta_file, encoding="utf-8") as f:
                data = json.load(f)
            modified = False
            for _doc_id, meta in data.items():
                if "user_id" not in meta:
                    meta["user_id"] = "usr_admin"
                    meta["username"] = "admin"
                    modified = True
            if modified:
                with open(self.docs_meta_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error migrating docs metadata: {e}")

    def _split_into_chunks(self, text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    overlap_text = (
                        current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    )
                    current_chunk = f"{overlap_text}\n\n{para}"
                else:
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    sub_chunk = ""
                    for s in sentences:
                        if len(sub_chunk) + len(s) + 1 <= chunk_size:
                            sub_chunk = f"{sub_chunk} {s}" if sub_chunk else s
                        else:
                            if sub_chunk:
                                chunks.append(sub_chunk)
                                sub_chunk = s
                            else:
                                chunks.append(s[:chunk_size])
                                sub_chunk = s[chunk_size:]
                    if sub_chunk:
                        current_chunk = sub_chunk

        if current_chunk:
            chunks.append(current_chunk)

        return [c.strip() for c in chunks if len(c.strip()) > 30]

    async def _get_ollama_embeddings(self, texts: list[str]) -> list[list[float]] | None:
        """Try to get Ollama embeddings; return None if unavailable (graceful fallback)."""
        try:
            embeddings = []
            async with httpx.AsyncClient(timeout=1.5) as client:
                for t in texts:
                    res = await client.post(
                        f"{settings.ollama_base_url}/api/embeddings",
                        json={"model": settings.ollama_embed_model, "prompt": t},
                    )
                    if res.status_code == 200:
                        embeddings.append(res.json().get("embedding"))
                    else:
                        return None
            return embeddings
        except Exception:
            return None

    async def add_document(
        self,
        doc_id: str,
        filename: str,
        pages_data: list[dict[str, Any]],
        meta: dict[str, Any],
        user_id: str = "usr_admin",
        username: str = "admin",
    ) -> int:
        all_chunks: list[str] = []
        ids: list[str] = []
        metadatas: list[dict] = []
        chunk_idx = 0

        for page_info in pages_data:
            page_num = page_info["page"]
            text = page_info["text"]
            chunks = self._split_into_chunks(text, settings.chunk_size, settings.chunk_overlap)

            for c in chunks:
                chunk_id = f"{doc_id}_{chunk_idx}"
                all_chunks.append(c)
                ids.append(chunk_id)
                metadatas.append(
                    {
                        "document_id": doc_id,
                        "filename": filename,
                        "page": page_num,
                        "chunk_index": chunk_idx,
                        "user_id": user_id,
                        "username": username,
                    }
                )
                chunk_idx += 1

        if not all_chunks:
            all_chunks.append(f"Document {filename} contains minimal readable text.")
            ids.append(f"{doc_id}_0")
            metadatas.append(
                {
                    "document_id": doc_id,
                    "filename": filename,
                    "page": 1,
                    "chunk_index": 0,
                    "user_id": user_id,
                    "username": username,
                }
            )
            chunk_idx = 1

        self.store.add(ids=ids, documents=all_chunks, metadatas=metadatas)

        self._save_document_meta(
            doc_id,
            {
                "id": doc_id,
                "filename": filename,
                "upload_date": meta.get("upload_date"),
                "file_size": meta.get("file_size", 0),
                "page_count": meta.get("page_count", 1),
                "chunk_count": chunk_idx,
                "summary": meta.get("summary", ""),
                "user_id": user_id,
                "username": username,
            },
        )

        return chunk_idx

    def _save_document_meta(self, doc_id: str, meta: dict[str, Any]):
        try:
            with open(self.docs_meta_file, encoding="utf-8") as f:
                data = json.load(f)
            data[doc_id] = meta
            with open(self.docs_meta_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving doc metadata: {e}")

    def get_all_documents(self) -> list[dict[str, Any]]:
        try:
            with open(self.docs_meta_file, encoding="utf-8") as f:
                data = json.load(f)
            return list(data.values())
        except Exception:
            return []

    def get_documents_for_user(self, user_id: str, is_admin: bool = False) -> list[dict[str, Any]]:
        all_docs = self.get_all_documents()
        if is_admin:
            return all_docs
        return [d for d in all_docs if d.get("user_id") == user_id]

    def get_document_by_id(
        self, doc_id: str, user_id: str | None = None, is_admin: bool = False
    ) -> dict[str, Any] | None:
        try:
            with open(self.docs_meta_file, encoding="utf-8") as f:
                data = json.load(f)
            doc = data.get(doc_id)
            if not doc:
                return None
            if is_admin or user_id is None or doc.get("user_id") == user_id:
                return doc
            return None
        except Exception:
            return None

    def delete_document(
        self, doc_id: str, user_id: str | None = None, is_admin: bool = False
    ) -> bool:
        doc = self.get_document_by_id(doc_id, user_id=user_id, is_admin=is_admin)
        if not doc:
            return False

        self.store.delete(document_id=doc_id)

        try:
            with open(self.docs_meta_file, encoding="utf-8") as f:
                data = json.load(f)
            if doc_id in data:
                del data[doc_id]
                with open(self.docs_meta_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    async def query_relevant_chunks(
        self,
        query: str,
        document_id: str | None = None,
        user_id: str | None = None,
        is_admin: bool = False,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        # When a specific document is requested, verify ownership first
        if document_id:
            doc = self.get_document_by_id(document_id, user_id=user_id, is_admin=is_admin)
            if not doc:
                return []

        results = self.store.query(
            query_text=query,
            n_results=n_results,
            document_id=document_id,
            user_id=user_id,
            is_admin=is_admin,
        )
        return [
            {
                "text": r["text"],
                "document_id": r["meta"].get("document_id", ""),
                "filename": r["meta"].get("filename", "Unknown Document"),
                "page": r["meta"].get("page", 1),
                "chunk_index": r["meta"].get("chunk_index", 0),
                "similarity": r["similarity"],
                "user_id": r["meta"].get("user_id", ""),
            }
            for r in results
        ]

    def get_document_full_text(
        self, doc_id: str, user_id: str | None = None, is_admin: bool = False
    ) -> str:
        doc = self.get_document_by_id(doc_id, user_id=user_id, is_admin=is_admin)
        if not doc:
            return ""
        chunks = self.store.get_chunks_for_doc(doc_id)
        return "\n\n".join(c["text"] for c in chunks)

    def _read_stats_raw(self) -> dict[str, Any]:
        try:
            with open(self.stats_file, encoding="utf-8") as f:
                raw = json.load(f)
            if "users" not in raw:
                legacy_tests = raw.get("tests_taken", 0)
                legacy_sum = raw.get("total_score_sum", 0)
                legacy_ans = raw.get("total_questions_answered", 0)
                legacy_rev = raw.get("topics_revised", 0)
                migrated = {
                    "global": {
                        "tests_taken": legacy_tests,
                        "total_score_sum": legacy_sum,
                        "total_questions_answered": legacy_ans,
                        "topics_revised": legacy_rev,
                    },
                    "users": {
                        "usr_admin": {
                            "tests_taken": legacy_tests,
                            "total_score_sum": legacy_sum,
                            "total_questions_answered": legacy_ans,
                            "topics_revised": legacy_rev,
                        }
                    },
                }
                with open(self.stats_file, "w", encoding="utf-8") as f:
                    json.dump(migrated, f, indent=2)
                return migrated
            return raw
        except Exception:
            return {
                "global": {
                    "tests_taken": 0,
                    "total_score_sum": 0,
                    "total_questions_answered": 0,
                    "topics_revised": 0,
                },
                "users": {},
            }

    def get_stats_for_user(
        self, user_id: str | None = None, is_admin: bool = False
    ) -> dict[str, Any]:
        stats = self._read_stats_raw()
        if is_admin and not user_id:
            g = stats.get("global", {})
            tests_taken = g.get("tests_taken", 0)
            avg_score = 0.0
            if tests_taken > 0 and g.get("total_questions_answered", 0) > 0:
                avg_score = round(
                    (g.get("total_score_sum", 0) / g.get("total_questions_answered", 0)) * 100, 1
                )
            docs = self.get_all_documents()
            return {
                "documents_uploaded": len(docs),
                "tests_taken": tests_taken,
                "avg_score": avg_score,
                "topics_revised": g.get("topics_revised", 0),
            }

        user_id = user_id or "usr_admin"
        u_stats = stats.get("users", {}).get(
            user_id,
            {
                "tests_taken": 0,
                "total_score_sum": 0,
                "total_questions_answered": 0,
                "topics_revised": 0,
            },
        )
        tests_taken = u_stats.get("tests_taken", 0)
        avg_score = 0.0
        if tests_taken > 0 and u_stats.get("total_questions_answered", 0) > 0:
            avg_score = round(
                (u_stats.get("total_score_sum", 0) / u_stats.get("total_questions_answered", 0))
                * 100,
                1,
            )

        user_docs = self.get_documents_for_user(user_id, is_admin=False)
        return {
            "documents_uploaded": len(user_docs),
            "tests_taken": tests_taken,
            "avg_score": avg_score,
            "topics_revised": u_stats.get("topics_revised", 0),
        }

    def record_test_result(self, score: int, total_questions: int, user_id: str = "usr_admin"):
        try:
            stats = self._read_stats_raw()
            g = stats.setdefault(
                "global",
                {
                    "tests_taken": 0,
                    "total_score_sum": 0,
                    "total_questions_answered": 0,
                    "topics_revised": 0,
                },
            )
            g["tests_taken"] = g.get("tests_taken", 0) + 1
            g["total_score_sum"] = g.get("total_score_sum", 0) + score
            g["total_questions_answered"] = g.get("total_questions_answered", 0) + total_questions

            users_dict = stats.setdefault("users", {})
            u = users_dict.setdefault(
                user_id,
                {
                    "tests_taken": 0,
                    "total_score_sum": 0,
                    "total_questions_answered": 0,
                    "topics_revised": 0,
                },
            )
            u["tests_taken"] = u.get("tests_taken", 0) + 1
            u["total_score_sum"] = u.get("total_score_sum", 0) + score
            u["total_questions_answered"] = u.get("total_questions_answered", 0) + total_questions

            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            print(f"Error updating test stats: {e}")

    def increment_topics_revised(self, user_id: str = "usr_admin"):
        try:
            stats = self._read_stats_raw()
            g = stats.setdefault(
                "global",
                {
                    "tests_taken": 0,
                    "total_score_sum": 0,
                    "total_questions_answered": 0,
                    "topics_revised": 0,
                },
            )
            g["topics_revised"] = g.get("topics_revised", 0) + 1

            users_dict = stats.setdefault("users", {})
            u = users_dict.setdefault(
                user_id,
                {
                    "tests_taken": 0,
                    "total_score_sum": 0,
                    "total_questions_answered": 0,
                    "topics_revised": 0,
                },
            )
            u["topics_revised"] = u.get("topics_revised", 0) + 1

            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            print(f"Error updating revision stats: {e}")


vector_service = VectorService()
