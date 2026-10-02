from app.config import AppSettings, settings


def test_cors_config_parsing():
    cfg1 = AppSettings(allowed_origins="http://example.com, http://test.com")
    assert cfg1.allowed_origins == ["http://example.com", "http://test.com"]

    cfg2 = AppSettings(allowed_origins="*")
    assert cfg2.allowed_origins == ["*"]


def test_upload_invalid_magic_bytes_rejected(client, auth_headers):
    # Has .pdf extension but invalid header
    fake_pdf = b"NOT_A_REAL_PDF_HEADER_JUST_RANDOM_TEXT"
    res = client.post(
        "/api/upload",
        headers=auth_headers,
        files={"file": ("fake.pdf", fake_pdf, "application/pdf")},
    )
    assert res.status_code == 400
    data = res.json()
    assert "magic header" in data["detail"].lower()
    assert data["status_code"] == 400


def test_upload_oversized_file_rejected(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_size_bytes", 100)
    oversized_pdf = b"%PDF-1.4 " + (b"A" * 200)
    res = client.post(
        "/api/upload",
        headers=auth_headers,
        files={"file": ("large.pdf", oversized_pdf, "application/pdf")},
    )
    assert res.status_code == 413
    data = res.json()
    assert "exceeds maximum" in data["detail"].lower()
    assert data["status_code"] == 413


def test_consistent_error_structure_on_404(client, auth_headers):
    res = client.get("/api/documents/non_existent_doc_id/download", headers=auth_headers)
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data
    assert data["status_code"] == 404
    assert data["path"] == "/api/documents/non_existent_doc_id/download"


def test_consistent_error_structure_on_validation_error(client, auth_headers):
    # Missing required body field
    res = client.post("/api/quiz/generate", headers=auth_headers, json={})
    assert res.status_code == 422
    data = res.json()
    assert "errors" in data
    assert data["status_code"] == 422
    assert "detail" in data


def test_safe_filename_sanitization(client, auth_headers, sample_pdf_bytes):
    # Path traversal attempt in filename
    res = client.post(
        "/api/upload",
        headers=auth_headers,
        files={"file": ("../../etc/passwd.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 200
    doc = res.json()
    assert "/" not in doc["filename"]
    assert "\\" not in doc["filename"]
    assert ".." not in doc["filename"]
