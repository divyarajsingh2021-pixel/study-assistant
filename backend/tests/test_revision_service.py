import pytest
from app.services.revision_service import revision_service
from app.services.vector_service import vector_service


@pytest.mark.asyncio
async def test_generate_revision_sheet():
    doc_id = "doc_rev_test"
    pages_data = [
        {
            "page": 1,
            "text": "Process synchronization is defined as the coordination of simultaneous processes to complete a task.",
        },
        {
            "page": 2,
            "text": "Race condition refers to a situation where the output depends on the execution sequence of threads.",
        },
    ]
    await vector_service.add_document(
        doc_id=doc_id,
        filename="Synchronization.pdf",
        pages_data=pages_data,
        meta={"file_size": 1024, "page_count": 2},
        user_id="usr_admin",
        username="admin",
    )

    sheet = await revision_service.generate_revision_sheet(
        document_id=doc_id, topic="Process Synchronization", user_id="usr_admin", is_admin=True
    )

    assert sheet.document_id == doc_id
    assert len(sheet.key_definitions) > 0
    assert len(sheet.key_points) > 0
    assert len(sheet.example_qas) > 0
    assert "# One-Shot Revision Sheet" in sheet.raw_markdown


@pytest.mark.asyncio
async def test_generate_revision_unauthorized_doc():
    with pytest.raises(ValueError) as exc_info:
        await revision_service.generate_revision_sheet(
            document_id="missing_doc_id", topic="Test", user_id="usr_student1", is_admin=False
        )
    assert "not found or not authorized" in str(exc_info.value)
