import pytest
from app.services.quiz_service import quiz_service
from app.services.vector_service import vector_service


@pytest.mark.asyncio
async def test_generate_quiz_offline_fallback():
    doc_id = "doc_quiz_test"
    pages_data = [
        {
            "page": 1,
            "text": "Mutual exclusion refers to the requirement that one process may use a resource at a time.",
        },
        {
            "page": 1,
            "text": "Hold and wait is a condition where processes hold resources while waiting for additional resources.",
        },
        {
            "page": 2,
            "text": "A semaphore is a synchronization variable used to control access to common resources.",
        },
    ]
    await vector_service.add_document(
        doc_id=doc_id,
        filename="Concurrency_Notes.pdf",
        pages_data=pages_data,
        meta={"file_size": 2048, "page_count": 2},
        user_id="usr_admin",
        username="admin",
    )

    quiz = await quiz_service.generate_quiz(
        document_id=doc_id, topic="Deadlocks", num_questions=3, user_id="usr_admin", is_admin=True
    )

    assert quiz.document_id == doc_id
    assert len(quiz.questions) == 3
    for q in quiz.questions:
        assert len(q.options) == 4
        assert 0 <= q.correct_answer <= 3
        assert len(q.explanation) > 0


@pytest.mark.asyncio
async def test_generate_quiz_unauthorized_document():
    with pytest.raises(ValueError) as exc_info:
        await quiz_service.generate_quiz(
            document_id="non_existent_doc",
            topic="Test",
            num_questions=3,
            user_id="usr_student1",
            is_admin=False,
        )
    assert "not found or not authorized" in str(exc_info.value)
