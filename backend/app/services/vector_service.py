import json
import re
from pathlib import Path
from typing import Any

import chromadb
import httpx
from app.config import CHROMA_DIR, DATA_DIR, settings
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

DOCS_META_FILE = DATA_DIR / "documents_meta.json"
STATS_FILE = DATA_DIR / "stats.json"


class VectorService:
    def __init__(self, data_dir: Path | None = None, chroma_dir: Path | None = None):
        self.data_dir = data_dir or DATA_DIR
        self.chroma_dir = chroma_dir or CHROMA_DIR
        self.docs_meta_file = self.data_dir / "documents_meta.json"
        self.stats_file = self.data_dir / "stats.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self._init_storage()
        self._init_chroma()
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
        """
        Ensures existing legacy documents have user_id and username (default to admin)
        so no existing data is lost or broken.
        """
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

    def _init_chroma(self):
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_dir), settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.default_ef = embedding_functions.DefaultEmbeddingFunction()

        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.chroma_collection_name,
            embedding_function=self.default_ef,
            metadata={"hnsw:space": "cosine"},
        )

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
        all_chunks = []
        ids = []
        metadatas = []
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

        ollama_embs = await self._get_ollama_embeddings(all_chunks)
        if ollama_embs and len(ollama_embs) == len(all_chunks):
            self.collection.add(
                ids=ids, documents=all_chunks, embeddings=ollama_embs, metadatas=metadatas
            )
        else:
            self.collection.add(ids=ids, documents=all_chunks, metadatas=metadatas)

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

        try:
            self.collection.delete(where={"document_id": doc_id})
        except Exception as e:
            print(f"Error deleting from Chroma: {e}")

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
        where_filter = None
        if document_id:
            doc = self.get_document_by_id(document_id, user_id=user_id, is_admin=is_admin)
            if not doc:
                return []
            where_filter = {"document_id": document_id}
        elif user_id and not is_admin:
            where_filter = {"user_id": user_id}

        query_embs = await self._get_ollama_embeddings([query])
        if query_embs:
            results = self.collection.query(
                query_embeddings=query_embs, n_results=n_results, where=where_filter
            )
        else:
            results = self.collection.query(
                query_texts=[query], n_results=n_results, where=where_filter
            )

        output = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []

            for i, doc_text in enumerate(docs):
                meta = metas[i] if i < len(metas) else {}
                dist = distances[i] if i < len(distances) else 0.0
                similarity = round(max(0.0, 1.0 - float(dist)), 4) if dist is not None else 0.85
                output.append(
                    {
                        "text": doc_text,
                        "document_id": meta.get("document_id", ""),
                        "filename": meta.get("filename", "Unknown Document"),
                        "page": meta.get("page", 1),
                        "chunk_index": meta.get("chunk_index", 0),
                        "similarity": similarity,
                        "user_id": meta.get("user_id", ""),
                    }
                )
        return output

    def get_document_full_text(
        self, doc_id: str, user_id: str | None = None, is_admin: bool = False
    ) -> str:
        doc = self.get_document_by_id(doc_id, user_id=user_id, is_admin=is_admin)
        if not doc:
            return ""

        try:
            results = self.collection.get(
                where={"document_id": doc_id}, include=["documents", "metadatas"]
            )
            if not results or not results.get("documents"):
                return ""

            combined = []
            for doc_chunk, meta in zip(results["documents"], results["metadatas"], strict=False):
                combined.append((meta.get("chunk_index", 0), doc_chunk))
            combined.sort(key=lambda x: x[0])
            return "\n\n".join(item[1] for item in combined)
        except Exception as e:
            print(f"Error fetching full text: {e}")
            return ""

    def _read_stats_raw(self) -> dict[str, Any]:
        try:
            with open(self.stats_file, encoding="utf-8") as f:
                raw = json.load(f)
            if "users" not in raw:
                # Migrate legacy flat stats
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
            # Update global
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

            # Update per-user
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
