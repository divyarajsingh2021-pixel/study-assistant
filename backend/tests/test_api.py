import pytest
from app.services.vector_service import vector_service


def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"


def test_api_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "active_provider" in data


def test_auth_login_endpoint(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    assert "token" in res.json()


def test_auth_login_invalid_credentials(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401


def test_unauthorized_access_blocked(client):
    res = client.get("/api/documents")
    assert res.status_code == 401


def test_upload_non_pdf_rejected(client, auth_headers):
    res = client.post(
        "/api/upload",
        headers=auth_headers,
        files={"file": ("test.txt", b"plain text", "text/plain")},
    )
    assert res.status_code == 400
    assert "Only PDF files" in res.json()["detail"]


def test_document_lifecycle_upload_download_delete(client, auth_headers, sample_pdf_bytes):
    # Upload
    upload_res = client.post(
        "/api/upload",
        headers=auth_headers,
        files={"file": ("Sample_Test_Notes.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 200
    doc = upload_res.json()
    doc_id = doc["id"]
    assert doc["filename"] == "Sample_Test_Notes.pdf"
    assert doc["page_count"] == 2

    # List documents
    list_res = client.get("/api/documents", headers=auth_headers)
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)

    # Download document
    dl_res = client.get(f"/api/documents/{doc_id}/download", headers=auth_headers)
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"

    # Delete document
    del_res = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["document_id"] == doc_id

    # Verify deleted
    list_after = client.get("/api/documents", headers=auth_headers)
    assert not any(d["id"] == doc_id for d in list_after.json()["documents"])


@pytest.mark.asyncio
async def test_full_study_workflow(client, auth_headers):
    # Seed document directly in vector_service
    doc_id = "wf_doc_1"
    pages_data = [
        {
            "page": 1,
            "text": "Operating systems manage CPU scheduling, memory management, and file systems.",
        },
        {
            "page": 2,
            "text": "A deadlock occurs when a set of processes are waiting for an event that only another process can trigger.",
        },
    ]
    await vector_service.add_document(
        doc_id=doc_id,
        filename="OS_Concepts.pdf",
        pages_data=pages_data,
        meta={"file_size": 2048, "page_count": 2, "upload_date": "Today"},
        user_id="usr_admin",
        username="admin",
    )

    # 1. RAG Chat
    chat_res = client.post(
        "/api/chat",
        headers=auth_headers,
        json={"question": "What is a deadlock?", "document_id": doc_id, "history": []},
    )
    assert chat_res.status_code == 200
    chat_json = chat_res.json()
    assert len(chat_json["answer"]) > 0
    assert len(chat_json["citations"]) > 0

    # 2. Quiz Generation
    quiz_res = client.post(
        "/api/quiz/generate",
        headers=auth_headers,
        json={"document_id": doc_id, "topic": "Deadlocks", "num_questions": 2},
    )
    assert quiz_res.status_code == 200
    quiz_json = quiz_res.json()
    assert len(quiz_json["questions"]) == 2

    # 3. Submit Quiz
    submit_res = client.post(
        "/api/quiz/submit",
        headers=auth_headers,
        json={
            "quiz_id": quiz_json["quiz_id"],
            "document_id": doc_id,
            "score": 2,
            "total_questions": 2,
        },
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["percentage"] == 100.0

    # 4. Revision Sheet
    rev_res = client.post(
        "/api/revision/generate",
        headers=auth_headers,
        json={"document_id": doc_id, "topic": "CPU Scheduling"},
    )
    assert rev_res.status_code == 200
    assert len(rev_res.json()["key_definitions"]) > 0

    # 5. Stats
    stats_res = client.get("/api/stats", headers=auth_headers)
    assert stats_res.status_code == 200
    stats_json = stats_res.json()
    assert stats_json["tests_taken"] == 1
    assert stats_json["avg_score"] == 100.0
