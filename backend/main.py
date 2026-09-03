import os
import shutil
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import rag_engine as rag

app = FastAPI(title="Study Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


class AskRequest(BaseModel):
    question: str


class QuizRequest(BaseModel):
    num_questions: int = 5


@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    total_chunks = 0
    processed = []
    for file in files:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        try:
            chunks = rag.add_document(tmp_path, file.filename)
            total_chunks += chunks
            processed.append({"filename": file.filename, "chunks": chunks})
        finally:
            os.unlink(tmp_path)
    return {"processed": processed, "total_chunks": total_chunks}


@app.post("/api/reset")
async def reset():
    rag.reset_collection()
    return {"status": "cleared"}


@app.post("/api/ask")
async def ask(req: AskRequest):
    try:
        return rag.answer_question(req.question)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/summarize")
async def summarize():
    try:
        return {"summary": rag.summarize_notes()}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/quiz")
async def quiz(req: QuizRequest):
    try:
        questions = rag.generate_quiz(req.num_questions)
        return {"questions": questions}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Serve the frontend ---
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
