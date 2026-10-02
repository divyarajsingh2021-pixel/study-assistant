import pytest
from app.services.vector_service import vector_service


def test_chunking_logic_short_text():
    text = "Short paragraph about operating systems. Process synchronization is critical."
    chunks = vector_service._split_into_chunks(text, chunk_size=800, overlap=150)
    assert len(chunks) == 1
    assert "operating systems" in chunks[0]


def test_chunking_logic_long_text_overlap():
    long_para = "Operating systems manage hardware resources. " * 30
    chunks = vector_service._split_into_chunks(long_para, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    # Check that chunks have reasonable lengths
    for chunk in chunks:
        assert len(chunk) > 30


@pytest.mark.asyncio
async def test_add_and_query_document():
    doc_id = "doc_test_1"
    pages_data = [
        {
            "page": 1,
            "text": "Deadlock is a situation where a set of processes are blocked because each process is holding a resource.",
        },
        {
            "page": 2,
            "text": "Semaphores and mutex locks are synchronization tools used to prevent race conditions.",
        },
    ]
    meta = {"file_size": 1024, "page_count": 2, "upload_date": "Today"}

    chunk_count = await vector_service.add_document(
        doc_id=doc_id,
        filename="OS_Notes.pdf",
        pages_data=pages_data,
        meta=meta,
        user_id="usr_admin",
        username="admin",
    )

    assert chunk_count >= 2

    # Query for deadlock
    results = await vector_service.query_relevant_chunks(
        query="What is a deadlock?", document_id=doc_id, user_id="usr_admin", is_admin=True
    )
    assert len(results) > 0
    assert "deadlock" in results[0]["text"].lower()
    assert results[0]["page"] == 1


@pytest.mark.asyncio
async def test_document_user_isolation():
    await vector_service.add_document(
        doc_id="user1_doc",
        filename="User1_Notes.pdf",
        pages_data=[{"page": 1, "text": "Private notes belonging to student 1."}],
        meta={"file_size": 500, "page_count": 1},
        user_id="usr_student1",
        username="student1",
    )

    # Student 1 gets their doc
    s1_docs = vector_service.get_documents_for_user("usr_student1", is_admin=False)
    assert len(s1_docs) == 1
    assert s1_docs[0]["id"] == "user1_doc"

    # Student 2 should see 0 docs
    s2_docs = vector_service.get_documents_for_user("usr_student2", is_admin=False)
    assert len(s2_docs) == 0

    # Direct query by Student 2 should return empty
    s2_query = await vector_service.query_relevant_chunks(
        query="Private notes", document_id="user1_doc", user_id="usr_student2", is_admin=False
    )
    assert len(s2_query) == 0


def test_stats_tracking_and_aggregation():
    vector_service.record_test_result(score=4, total_questions=5, user_id="usr_student1")
    vector_service.record_test_result(score=5, total_questions=5, user_id="usr_student1")
    vector_service.increment_topics_revised(user_id="usr_student1")

    stats = vector_service.get_stats_for_user(user_id="usr_student1", is_admin=False)
    assert stats["tests_taken"] == 2
    assert stats["avg_score"] == 90.0
    assert stats["topics_revised"] == 1


def test_delete_document():
    doc = vector_service.get_document_by_id("non_existent_doc")
    assert doc is None
    deleted = vector_service.delete_document("non_existent_doc")
    assert deleted is False
