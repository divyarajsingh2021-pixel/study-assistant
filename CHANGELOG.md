# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.1.0] - 2026-10-02

### Added

**Comprehensive Pytest Suite (`backend/tests/`)**
- Unit tests for PDF extraction, vector chunking, RAG citation assembly, quiz generation, revision synthesis, authentication, and multi-tenant document isolation.
- Isolated test fixtures using temporary in-memory vector storage to avoid cross-test contamination.
- 78% code coverage measured via `pytest-cov`.

**Docker & Compose**
- Production-ready `backend/Dockerfile` — non-root user, `/health` probe, `uvicorn` entrypoint.
- Multi-stage `frontend/Dockerfile` — Vite build followed by Nginx serving with SPA fallback routing.
- Root `docker-compose.yml` for single-command `docker compose up --build` deployment.
- Backend health check (`curl -f http://localhost:8000/health`) required before frontend starts.

**GitHub Actions CI**
- `.github/workflows/ci.yml` — three jobs: Backend Lint & Pytest, Frontend Build Check, Docker Build Validation.
- Offline RAG evaluation harness runs as part of the backend CI job (no API keys required).
- Dependabot configured for pip, npm, and GitHub Actions dependency updates.

**RAG Evaluation Harness (honest v2 benchmark)**
- Expanded corpus: 6 diverse AI-authored documents (OS Concurrency, Distributed Systems, Database ACID, Networking Protocols, Macroeconomics, Cell Biology) replacing the original single-document corpus.
- Rebuilt golden dataset: 72 questions in 5 categories (direct lookup, paraphrased, multi-chunk, cross-document distractor, unanswerable), split 36 dev / 36 held-out test.
- Audit of the original 25 questions: 36% (9/25) flagged for >70% word overlap or verbatim 4-gram copying — root cause of the original 100% MRR result.
- Metrics: Hit@1/3/5, MRR, per-category breakdown, abstention recall/precision/false-answer rate, average latency.
- 95% Wilson confidence intervals on all proportional metrics.
- `per_query_results.json` — full per-query rank, top-5 candidates with similarity scores, abstention decisions.
- Honest CI gate: Hit@3 ≥ 80%, MRR ≥ 0.75, calibrated from the new multi-document baseline.
- `backend/eval/README.md` — methodology, corpus sources (all AI-authored / public domain), and limitation disclosures.

**Production Hardening**
- PDF magic-byte (`%PDF-`) validation before any processing.
- File size cap enforced at upload (configurable via `MAX_UPLOAD_SIZE_MB`, default 25 MB).
- Filename sanitisation: `re.sub(r"[^a-zA-Z0-9_.-]", "_", ...)` to prevent path traversal.
- Rate limiting via `slowapi`: 120 req/min default, 15 req/min uploads, 45 req/min LLM endpoints.
- Structured request logging with per-request latency (milliseconds) via middleware.
- Consistent JSON error responses for `HTTPException` and `RequestValidationError`.
- Environment-based configuration via `pydantic-settings` (`AppSettings`), replacing ad-hoc `os.getenv` calls.

**Documentation**
- `README.md` — complete rewrite with Mermaid architecture diagram, honest evaluation table, Docker and local quickstart, configuration table, full API reference, design decisions, and known limitations.
- `CONTRIBUTING.md` — fork, setup, branch naming, commit message conventions, pre-PR checklist.
- `CHANGELOG.md` (this file) in Keep a Changelog format.
- `LICENSE` — MIT, with a [Your Name] placeholder.
- `.github/ISSUE_TEMPLATE/bug_report.md` and `feature_request.md`.
- `docs/images/` — placeholder files with screenshot capture instructions.
- `docs/RELEASE_NOTES_v1.1.0.md` — narrative release notes.

### Changed

- `VectorService` and `AuthService` refactored to accept injected storage directory paths, enabling isolated test fixtures.
- UI description in documentation updated to neutral language; legacy ERP design-system references removed.
- Test infrastructure migrated from ad-hoc scripts to standard pytest framework.
- CHANGELOG entry for v1.1.0 updated: the evaluation harness entry now reflects the honest v2 benchmark (6-document corpus, 72 questions, Wilson CIs) rather than the original single-document 25-question harness.

### Fixed

- Abstention failure explanation in `eval/results.md` corrected: Q67 (*quantum packet routing*) had similarity 0.4287 — **above** threshold — due to lexical overlap on "packet", "routing", "IP", "protocol". Previous text incorrectly described this as "weak similarity".

---

## [1.0.0] - 2026-09-15

### Added

- Initial release of AI Study Assistant.
- FastAPI backend with ChromaDB vector search and multi-tier LLM fallback (Ollama → Groq → heuristic engine).
- React 18 + Vite + Tailwind CSS frontend.
- Grounded RAG Chat with exact document and page citations.
- Interactive Mock Test Generator with MCQ scoring.
- One-Shot Revision Sheet synthesis with PDF/print export.
- Role-based multi-user authentication with per-user isolated study libraries.
- Deployment on Vercel (frontend) and Render (backend).
