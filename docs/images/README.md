# Screenshots & Demo GIF Capture Guide

This directory contains visual assets for the project documentation. When capturing assets, use the live deployment at [https://study-assistant-sooty.vercel.app](https://study-assistant-sooty.vercel.app) or a clean local instance running at `http://localhost:5173`.

---

## Required Visual Assets

### 1. `01_document_library.png`
- **What to capture:** The main Document Library / Dashboard view.
- **State to prepare:**
  - Log in as a student or admin user.
  - Upload 1–2 sample PDFs (e.g. `Operating_Systems_Concurrency.pdf`).
  - Ensure the document card displays: title, page count, chunk count, upload timestamp, and the action buttons (Chat, Mock Test, Revision Sheet, Delete).
- **Dimensions / Format:** 1920x1080 (16:9) or 1280x720, PNG format, clean browser frame without extraneous bookmarks or personal tabs.

---

### 2. `02_rag_chat.png`
- **What to capture:** The Grounded RAG Chat interface with a complete question-and-answer exchange.
- **State to prepare:**
  - Select an uploaded PDF.
  - Ask a specific question (e.g., *"What are the four Coffman conditions necessary for deadlock?"*).
  - Ensure the rendered answer shows:
    - The structured response text (bullet points or numbered list).
    - The citation banner showing Document Name, Page number, and similarity score.
    - The provider badge (e.g., `Ollama (llama3.1:latest)` or `Groq (llama-3.1-8b-instant)`).
- **Dimensions / Format:** 1920x1080 or 1280x720, PNG format.

---

### 3. `03_mock_test.png`
- **What to capture:** The Interactive Mock Test interface.
- **State to prepare:**
  - Generate a 5-question mock quiz on an uploaded document.
  - Select options for the questions and submit.
  - Capture the results screen showing:
    - Score display (e.g., `4/5 (80%)`).
    - The confetti animation or celebration banner.
    - Question review with correct answer badges and explanations.
- **Dimensions / Format:** 1920x1080 or 1280x720, PNG format.

---

### 4. `04_revision_sheet.png`
- **What to capture:** The One-Shot Revision Sheet view.
- **State to prepare:**
  - Generate a revision sheet for an uploaded document topic.
  - Capture the structured output showing:
    - Key definitions and core concepts.
    - Important formulas / rules / tables.
    - Common exam traps and FAQs.
    - The "Export PDF / Print" button.
- **Dimensions / Format:** 1920x1080 or 1280x720, PNG format.

---

### 5. `demo.gif`
- **What to capture:** A 15–30 second animated walkthrough of the core workflow.
- **Sequence to record:**
  1. Drag and drop a PDF into the upload area (shows upload progress and indexing).
  2. Switch to Chat tab and type a question.
  3. Show the answer appearing with exact page citation.
  4. Switch to Mock Test tab, answer one question, and show score.
- **Format:** GIF or MP4 (optimized, < 10 MB, 1280x720 at 24-30 fps). Recommended tool: ScreenToGif, Kap, or OBS Studio converted via ffmpeg.
