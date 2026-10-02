import uuid
from datetime import datetime

from app.config import UPLOADS_DIR, settings
from app.models.schemas import (
    AdminResetPasswordRequest,
    ChangePasswordRequest,
    ChatRequest,
    ChatResponse,
    DocumentInfo,
    DocumentListResponse,
    ForgotPasswordRequest,
    GenerateQuizRequest,
    GenerateRevisionRequest,
    HealthResponse,
    LoginRequest,
    LoginResponse,
    QuizResponse,
    RegisterUserRequest,
    RevisionResponse,
    SettingsUpdateRequest,
    StatsResponse,
    SubmitQuizRequest,
    UserItem,
)
from app.services.auth_service import auth_service
from app.services.llm_service import llm_service
from app.services.pdf_service import pdf_service
from app.services.quiz_service import quiz_service
from app.services.rag_service import rag_service
from app.services.revision_service import revision_service
from app.services.vector_service import vector_service
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(
    title="DSC AI Study & Exam Suite API",
    description="FastAPI backend for RAG study assistant, mock test generation, and user-isolated notes",
    version="2.0.0",
)

# Enable CORS for all frontends (Vite dev server + production Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- AUTH DEPENDENCY HELPERS -----------------


async def get_current_user_optional(
    authorization: str | None = Header(None), x_user_id: str | None = Header(None)
) -> dict | None:
    """
    Extracts authenticated user from Authorization Bearer token or fallback headers.
    """
    if authorization:
        user = auth_service.get_user_from_token(authorization)
        if user:
            return user
    if x_user_id:
        user = auth_service.get_user_by_id(x_user_id)
        if user:
            return user
    return None


async def get_current_user(
    authorization: str | None = Header(None), x_user_id: str | None = Header(None)
) -> dict:
    """
    Enforces authentication. Rejects request with 401 if token is missing or invalid.
    """
    user = await get_current_user_optional(authorization, x_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )
    return user


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Enforces admin role. Rejects non-admin users with 403 Forbidden.
    """
    if current_user.get("role") != "Admin" and current_user.get("username") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required for this action.",
        )
    return current_user


# ----------------- SYSTEM & HEALTH -----------------


@app.get("/")
@app.head("/")
async def root():
    return {"status": "online", "name": "DSC AI Backend", "version": "2.0.0"}


@app.get("/api/health", response_model=HealthResponse)
async def get_health(current_user: dict | None = Depends(get_current_user_optional)):
    provider_status = await llm_service.check_provider_status()
    if current_user and current_user.get("role") != "Admin":
        docs = vector_service.get_documents_for_user(current_user["id"], is_admin=False)
    else:
        docs = vector_service.get_all_documents()

    return HealthResponse(
        status="healthy",
        ollama_connected=provider_status["ollama_connected"],
        ollama_model_available=provider_status["ollama_model_available"],
        groq_configured=provider_status["groq_configured"],
        active_provider=provider_status["active_provider"],
        document_count=len(docs),
    )


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(current_user: dict = Depends(get_current_user)):
    is_admin = current_user.get("role") == "Admin"
    return vector_service.get_stats_for_user(user_id=current_user["id"], is_admin=is_admin)


@app.post("/api/settings")
async def update_settings(req: SettingsUpdateRequest, admin_user: dict = Depends(get_admin_user)):
    if req.ollama_base_url is not None:
        settings.ollama_base_url = req.ollama_base_url
    if req.ollama_model is not None:
        settings.ollama_model = req.ollama_model
    if req.ollama_embed_model is not None:
        settings.ollama_embed_model = req.ollama_embed_model
    if req.groq_api_key is not None:
        settings.groq_api_key = req.groq_api_key
    if req.groq_model is not None:
        settings.groq_model = req.groq_model
    if req.preferred_provider is not None:
        settings.preferred_provider = req.preferred_provider

    status_info = await llm_service.check_provider_status()
    return {"message": "Settings updated successfully", "status": status_info}


# ----------------- DOCUMENT MANAGEMENT (PER-USER ISOLATED) -----------------


@app.get("/api/documents", response_model=DocumentListResponse)
async def list_documents(current_user: dict = Depends(get_current_user)):
    is_admin = current_user.get("role") == "Admin"
    docs_data = vector_service.get_documents_for_user(user_id=current_user["id"], is_admin=is_admin)
    docs = [DocumentInfo(**d) for d in docs_data]
    return DocumentListResponse(documents=docs, total_count=len(docs))


@app.post("/api/upload", response_model=DocumentInfo)
async def upload_pdf(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files (.pdf) are supported."
        )

    doc_id = str(uuid.uuid4())[:12]
    safe_filename = file.filename.replace(" ", "_")
    target_path = UPLOADS_DIR / f"{doc_id}_{safe_filename}"

    try:
        contents = await file.read()
        with open(target_path, "wb") as f:
            f.write(contents)

        pages_data = pdf_service.extract_text_and_pages(target_path)
        meta = pdf_service.get_document_meta(target_path)
        upload_date = datetime.now().strftime("%b %d, %Y %I:%M %p")

        if not pages_data:
            pages_data = [{"page": 1, "text": f"Document: {file.filename}"}]

        chunk_count = await vector_service.add_document(
            doc_id=doc_id,
            filename=file.filename,
            pages_data=pages_data,
            meta={
                "upload_date": upload_date,
                "file_size": meta["file_size"],
                "page_count": meta["page_count"],
                "summary": f"{meta['page_count']} pages parsed",
            },
            user_id=current_user["id"],
            username=current_user["username"],
        )

        return DocumentInfo(
            id=doc_id,
            filename=file.filename,
            upload_date=upload_date,
            file_size=meta["file_size"],
            page_count=meta["page_count"],
            chunk_count=chunk_count,
            summary=f"Successfully indexed {chunk_count} chunks across {meta['page_count']} pages.",
            user_id=current_user["id"],
            username=current_user["username"],
        )

    except Exception as e:
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


@app.get("/api/documents/{doc_id}/download")
async def download_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    is_admin = current_user.get("role") == "Admin"
    doc_meta = vector_service.get_document_by_id(
        doc_id=doc_id, user_id=current_user["id"], is_admin=is_admin
    )
    if not doc_meta:
        raise HTTPException(
            status_code=404, detail="Document not found or you do not have permission to access it."
        )

    for f in UPLOADS_DIR.glob(f"{doc_id}_*"):
        if f.is_file():
            return FileResponse(
                path=str(f), filename=doc_meta["filename"], media_type="application/pdf"
            )

    raise HTTPException(status_code=404, detail="Original PDF file is missing on server")


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    is_admin = current_user.get("role") == "Admin"
    doc_meta = vector_service.get_document_by_id(
        doc_id=doc_id, user_id=current_user["id"], is_admin=is_admin
    )
    if not doc_meta:
        raise HTTPException(
            status_code=404, detail="Document not found or you do not have permission to delete it."
        )

    for f in UPLOADS_DIR.glob(f"{doc_id}_*"):
        try:
            f.unlink(missing_ok=True)
        except Exception:
            pass

    vector_service.delete_document(doc_id=doc_id, user_id=current_user["id"], is_admin=is_admin)
    return {"message": "Document deleted successfully", "document_id": doc_id}


# ----------------- MOCK TEST GENERATOR (USER ISOLATED) -----------------


@app.post("/api/quiz/generate", response_model=QuizResponse)
async def generate_mock_test(
    req: GenerateQuizRequest, current_user: dict = Depends(get_current_user)
):
    is_admin = current_user.get("role") == "Admin"
    doc = vector_service.get_document_by_id(
        doc_id=req.document_id, user_id=current_user["id"], is_admin=is_admin
    )
    if not doc:
        raise HTTPException(
            status_code=404, detail="Selected document not found in your study library."
        )

    try:
        quiz = await quiz_service.generate_quiz(
            document_id=req.document_id,
            topic=req.topic,
            num_questions=req.num_questions,
            user_id=current_user["id"],
            is_admin=is_admin,
        )
        return quiz
    except ValueError as ve:
        raise HTTPException(status_code=403, detail=str(ve))


@app.post("/api/quiz/submit")
async def submit_quiz(req: SubmitQuizRequest, current_user: dict = Depends(get_current_user)):
    vector_service.record_test_result(
        score=req.score, total_questions=req.total_questions, user_id=current_user["id"]
    )
    return {
        "message": "Quiz result recorded successfully",
        "score": req.score,
        "total": req.total_questions,
        "percentage": round((req.score / max(1, req.total_questions)) * 100, 1),
    }


# ----------------- ONE-SHOT REVISION (USER ISOLATED) -----------------


@app.post("/api/revision/generate", response_model=RevisionResponse)
async def generate_revision(
    req: GenerateRevisionRequest, current_user: dict = Depends(get_current_user)
):
    is_admin = current_user.get("role") == "Admin"
    doc = vector_service.get_document_by_id(
        doc_id=req.document_id, user_id=current_user["id"], is_admin=is_admin
    )
    if not doc:
        raise HTTPException(
            status_code=404, detail="Selected document not found in your study library."
        )

    try:
        sheet = await revision_service.generate_revision_sheet(
            document_id=req.document_id,
            topic=req.topic,
            user_id=current_user["id"],
            is_admin=is_admin,
        )
        return sheet
    except ValueError as ve:
        raise HTTPException(status_code=403, detail=str(ve))


# ----------------- GROUNDED RAG CHAT (USER ISOLATED) -----------------


@app.post("/api/chat", response_model=ChatResponse)
async def rag_chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    is_admin = current_user.get("role") == "Admin"
    if req.document_id:
        doc = vector_service.get_document_by_id(
            doc_id=req.document_id, user_id=current_user["id"], is_admin=is_admin
        )
        if not doc:
            raise HTTPException(
                status_code=404, detail="Selected document not found in your study library."
            )

    response = await rag_service.answer_question(
        question=req.question,
        document_id=req.document_id,
        history=req.history,
        user_id=current_user["id"],
        is_admin=is_admin,
    )
    return response


# ----------------- AUTHENTICATION & ROLE MANAGEMENT -----------------


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    user = auth_service.authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password. Please check your credentials.",
        )
    return LoginResponse(**user)


@app.post("/api/auth/change-password")
async def change_password(
    req: ChangePasswordRequest, current_user: dict = Depends(get_current_user)
):
    # Enforce that students can only change their own password
    if (
        current_user.get("role") != "Admin"
        and req.username.strip().lower() != current_user["username"].strip().lower()
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You can only change your own password."
        )
    try:
        auth_service.change_password(req.username, req.current_password, req.new_password)
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    try:
        auth_service.forgot_password_recovery(req.username, req.recovery_input, req.new_password)
        return {
            "message": "Password has been successfully reset. You can now log in with your new password."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- ADMIN-ONLY USER DIRECTORY & MANAGEMENT ROUTES ---


@app.get("/api/auth/users", response_model=list[UserItem])
async def list_users(admin_user: dict = Depends(get_admin_user)):
    users_data = auth_service.get_all_users(is_admin=True)
    return [UserItem(**u) for u in users_data]


@app.post("/api/auth/register", response_model=UserItem)
async def register_account(req: RegisterUserRequest, admin_user: dict = Depends(get_admin_user)):
    try:
        new_u = auth_service.register_user(
            username=req.username,
            password=req.password,
            name=req.name,
            email=req.email,
            role=req.role,
            recovery_code=req.recovery_code,
        )
        return UserItem(**new_u)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/auth/users/{username}")
async def delete_user(username: str, admin_user: dict = Depends(get_admin_user)):
    try:
        auth_service.delete_user(username)
        return {"message": f"Account '{username}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/admin-reset-password")
async def admin_reset_password(
    req: AdminResetPasswordRequest, admin_user: dict = Depends(get_admin_user)
):
    try:
        auth_service.admin_reset_password(req.target_username, req.new_password)
        return {"message": f"Password for '{req.target_username}' has been reset successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
