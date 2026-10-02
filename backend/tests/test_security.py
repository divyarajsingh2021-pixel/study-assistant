def test_admin_can_list_users_with_recovery_codes(client, auth_headers):
    res = client.get("/api/auth/users", headers=auth_headers)
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 5
    assert "recovery_code" in users[0]


def test_student_cannot_access_admin_routes(client, student_headers):
    # Cannot list users
    res = client.get("/api/auth/users", headers=student_headers)
    assert res.status_code == 403

    # Cannot delete user
    res = client.delete("/api/auth/users/student2", headers=student_headers)
    assert res.status_code == 403

    # Cannot change another user's password
    res = client.post(
        "/api/auth/change-password",
        headers=student_headers,
        json={"username": "student2", "current_password": "study123", "new_password": "hacked"},
    )
    assert res.status_code == 403


def test_cross_user_document_isolation(client, student_headers, sample_pdf_bytes):
    # Student 1 logs in and uploads doc
    upload_res = client.post(
        "/api/upload",
        headers=student_headers,
        files={"file": ("Student1_Private_Notes.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 200
    s1_doc_id = upload_res.json()["id"]

    # Student 2 logs in
    s2_login = client.post("/api/auth/login", json={"username": "student2", "password": "study123"})
    assert s2_login.status_code == 200
    s2_headers = {"Authorization": f"Bearer {s2_login.json()['token']}"}

    # Student 2 cannot see Student 1's doc in list
    s2_docs = client.get("/api/documents", headers=s2_headers).json()["documents"]
    assert not any(d["id"] == s1_doc_id for d in s2_docs)

    # Student 2 cannot download Student 1's doc
    dl_res = client.get(f"/api/documents/{s1_doc_id}/download", headers=s2_headers)
    assert dl_res.status_code in [403, 404]

    # Student 2 cannot delete Student 1's doc
    del_res = client.delete(f"/api/documents/{s1_doc_id}", headers=s2_headers)
    assert del_res.status_code in [403, 404]

    # Student 2 cannot generate quiz on Student 1's doc
    quiz_res = client.post(
        "/api/quiz/generate",
        headers=s2_headers,
        json={"document_id": s1_doc_id, "num_questions": 3},
    )
    assert quiz_res.status_code in [403, 404]

    # Student 2 cannot generate revision on Student 1's doc
    rev_res = client.post(
        "/api/revision/generate", headers=s2_headers, json={"document_id": s1_doc_id}
    )
    assert rev_res.status_code in [403, 404]
