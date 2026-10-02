from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    id: str
    filename: str
    upload_date: str
    file_size: int
    page_count: int
    chunk_count: int
    summary: str | None = ""
    user_id: str | None = None
    username: str | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total_count: int


class StatsResponse(BaseModel):
    documents_uploaded: int
    tests_taken: int
    avg_score: float
    topics_revised: int


class QuestionOption(BaseModel):
    id: str  # "A", "B", "C", "D"
    text: str


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: list[str]
    correct_answer: int  # 0, 1, 2, 3
    explanation: str
    source_snippet: str | None = None


class GenerateQuizRequest(BaseModel):
    document_id: str
    topic: str | None = None
    num_questions: int = Field(default=5, ge=1, le=20)


class QuizResponse(BaseModel):
    quiz_id: str
    document_id: str
    document_name: str
    topic: str | None = "General"
    questions: list[QuizQuestion]


class SubmitQuizRequest(BaseModel):
    quiz_id: str
    document_id: str
    score: int
    total_questions: int


class GenerateRevisionRequest(BaseModel):
    document_id: str
    topic: str | None = None


class RevisionQA(BaseModel):
    question: str
    answer: str


class RevisionResponse(BaseModel):
    document_id: str
    document_name: str
    topic: str
    key_definitions: list[dict[str, str]]
    key_points: list[str]
    example_qas: list[RevisionQA]
    raw_markdown: str | None = ""


class Citation(BaseModel):
    document_id: str
    document_name: str
    page: int
    snippet: str
    similarity_score: float | None = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    citations: list[Citation] | None = None


class ChatRequest(BaseModel):
    question: str
    document_id: str | None = None  # Specific doc or None for all
    history: list[ChatMessage] | None = []


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    provider_used: str


class SettingsUpdateRequest(BaseModel):
    ollama_base_url: str | None = None
    ollama_model: str | None = None
    ollama_embed_model: str | None = None
    groq_api_key: str | None = None
    groq_model: str | None = None
    preferred_provider: str | None = None


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    ollama_model_available: bool
    groq_configured: bool
    active_provider: str
    document_count: int


# Authentication Schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    id: str
    username: str
    name: str
    role: str
    email: str
    created_at: str
    token: str


class ChangePasswordRequest(BaseModel):
    username: str
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    username: str
    recovery_input: str  # email or recovery code
    new_password: str


class RegisterUserRequest(BaseModel):
    username: str
    password: str
    name: str
    email: str | None = ""
    role: str | None = "Student"
    recovery_code: str | None = ""


class UserItem(BaseModel):
    id: str
    username: str
    name: str
    role: str
    email: str
    created_at: str
    recovery_code: str | None = None


class AdminResetPasswordRequest(BaseModel):
    target_username: str
    new_password: str
