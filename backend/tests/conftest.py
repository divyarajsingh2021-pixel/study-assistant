import io

import chromadb
import pytest
from app.config import settings
from app.main import app
from app.services.auth_service import auth_service
from app.services.llm_service import llm_service
from app.services.vector_service import vector_service
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """
    Ensures every test runs against an isolated, clean temporary directory
    for ChromaDB, metadata JSON, and users JSON.
    """
    temp_data = tmp_path / "data"
    temp_chroma = temp_data / "chroma"
    temp_uploads = temp_data / "uploads"
    temp_users = temp_data / "users.json"
    temp_docs_meta = temp_data / "documents_meta.json"
    temp_stats = temp_data / "stats.json"

    temp_data.mkdir(parents=True, exist_ok=True)
    temp_chroma.mkdir(parents=True, exist_ok=True)
    temp_uploads.mkdir(parents=True, exist_ok=True)

    # Monkeypatch paths on singleton services
    monkeypatch.setattr(vector_service, "data_dir", temp_data)
    monkeypatch.setattr(vector_service, "chroma_dir", temp_chroma)
    monkeypatch.setattr(vector_service, "docs_meta_file", temp_docs_meta)
    monkeypatch.setattr(vector_service, "stats_file", temp_stats)

    # Reinitialize isolated ChromaDB in temporary directory
    temp_client = chromadb.PersistentClient(
        path=str(temp_chroma), settings=ChromaSettings(anonymized_telemetry=False)
    )
    temp_collection = temp_client.get_or_create_collection(
        name="test_collection",
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )
    monkeypatch.setattr(vector_service, "chroma_client", temp_client)
    monkeypatch.setattr(vector_service, "collection", temp_collection)
    vector_service._init_storage()

    # Reinitialize auth service in temporary directory
    monkeypatch.setattr(auth_service, "users_file", temp_users)
    auth_service._init_users_store()

    # Reset LLM service availability flags
    monkeypatch.setattr(llm_service, "ollama_available", False)
    monkeypatch.setattr(llm_service, "groq_available", False)
    monkeypatch.setattr(settings, "preferred_provider", "offline")
    monkeypatch.setattr(settings, "groq_api_key", "")

    yield {
        "data_dir": temp_data,
        "chroma_dir": temp_chroma,
        "uploads_dir": temp_uploads,
        "users_file": temp_users,
    }


@pytest.fixture
def client():
    """Returns FastAPI TestClient instance."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Logs in as admin and provides authorization bearer header."""
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_headers(client):
    """Logs in as student1 and provides authorization bearer header."""
    res = client.post("/api/auth/login", json={"username": "student1", "password": "study123"})
    assert res.status_code == 200
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_pdf_bytes():
    """Generates a valid 2-page PDF binary payload for testing."""
    import pypdf

    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.getvalue()
