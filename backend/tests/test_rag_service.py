import pytest
from app.models.schemas import ChatMessage
from app.services.rag_service import rag_service
from app.services.vector_service import vector_service


@pytest.mark.asyncio
async def test_rag_answer_with_citations():
    doc_id = "doc_rag_test"
    pages_data = [
        {
            "page": 1,
            "text": "Deadlock prevention ensures that at least one of the four necessary conditions cannot hold.",
        },
        {
            "page": 2,
            "text": "Circular wait condition can be prevented by imposing a total ordering of all resource types.",
        },
    ]
    await vector_service.add_document(
        doc_id=doc_id,
        filename="Deadlock_Guide.pdf",
        pages_data=pages_data,
        meta={"file_size": 1024, "page_count": 2},
        user_id="usr_admin",
        username="admin",
    )

    response = await rag_service.answer_question(
        question="How can circular wait condition be prevented?",
        document_id=doc_id,
        history=[ChatMessage(role="user", content="Hello")],
        user_id="usr_admin",
        is_admin=True,
    )

    assert len(response.answer) > 0
    assert len(response.citations) > 0
    assert response.citations[0].document_name == "Deadlock_Guide.pdf"
    assert response.citations[0].page in [1, 2]
    assert response.provider_used == "Local Heuristic Engine"


@pytest.mark.asyncio
async def test_rag_answer_no_documents_found():
    response = await rag_service.answer_question(
        question="What is quantum entanglement?",
        document_id=None,
        history=[],
        user_id="usr_student1",
        is_admin=False,
    )
    assert "couldn't find any relevant study material" in response.answer
    assert len(response.citations) == 0
