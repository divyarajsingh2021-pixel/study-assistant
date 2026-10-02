# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-10-02

### Added
- **RAG Evaluation Harness**:
  - Golden dataset with 25 curated question/answer/page triples from operating systems study notes.
  - Automated benchmark runner (`python -m eval.run`) measuring Hit@1, Hit@3, Hit@5, MRR, Citation Accuracy, Keyword Coverage, and Latency.
  - Offline deterministic execution and automated CI quality gate (`Hit@3 >= 80%`).
- **Comprehensive Pytest Suite (`backend/tests/`)**:
  - Unit tests for PDF extraction, vector chunking, RAG citations, quiz generator, revision syntheses, authentication, and multi-tenant security isolation.
  - Isolated test fixtures with temporary in-memory vector storage.
  - 78% code coverage verified via `pytest-cov`.
- **Production Hardening**:
  - PDF magic header verification and file size capping (25 MB).
  - Filename sanitization against path traversal.
  - Rate limiting via `slowapi` (`120/min` default, `15/min` uploads, `45/min` LLM endpoints).
  - Structured request logging with latency metrics and standardized error responses.
  - Environment-based configuration via `pydantic-settings`.
- **Docker & Compose**:
  - Production-ready `backend/Dockerfile` with non-root user and `/health` probe.
  - Multi-stage `frontend/Dockerfile` served via Nginx reverse proxy with SPA fallback.
  - Single-command orchestration via root `docker-compose.yml`.
- **CI/CD Automation**:
  - GitHub Actions CI workflow covering backend linting, pytest, RAG evaluation, frontend build, and Docker validation.
  - Dependabot automated updates for pip, npm, and GitHub Actions.

### Changed
- Refactored `VectorService` and `AuthService` to support dependency-injected storage directories for test isolation.
- Neutralized UI styling descriptions and removed legacy ERP references.
- Replaced custom script test runners with standard Pytest framework.

---

## [1.0.0] - 2026-09-15

### Added
- Initial release of AI Study Assistant.
- FastAPI backend with ChromaDB vector search and multi-tier LLM fallback (Ollama $\rightarrow$ Groq $\rightarrow$ Heuristic).
- React + Vite + Tailwind CSS frontend interface.
- Grounded RAG Chat with exact document and page citations.
- Interactive Mock Test Generator with MCQ scoring and confetti celebration.
- One-Shot Revision Sheet synthesis with PDF/print export.
- Role-based multi-user authentication and isolated study libraries.
