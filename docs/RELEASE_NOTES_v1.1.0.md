# Release Notes — AI Study Assistant v1.1.0

**Release Date:** October 2, 2026  
**Status:** Ready for Release (Do not tag until PR is merged)

AI Study Assistant v1.1.0 represents a major milestone in production readiness, testing rigor, automated CI/CD, and honest empirical evaluation of the Retrieval-Augmented Generation (RAG) pipeline.

---

## Highlights

1. **Rigorous RAG Evaluation Benchmark v2**:
   - Expanded the evaluation corpus from a single PDF to **6 diverse academic documents** (Operating Systems, Distributed Systems, Database ACID, Networking Protocols, Macroeconomics, Cell Biology) including distractors and a table-heavy document.
   - Built a 72-question golden set (36 dev / 36 held-out test) across 5 categories: direct lookup, paraphrased, multi-chunk, cross-document distractor, and unanswerable (abstention).
   - Audited the original 25 questions, discovering that **36% (9/25)** copied verbatim phrases or shared >70% word overlap with source chunks — explaining why the previous benchmark reported an unrealistic 100% MRR.
   - Replaced artificial perfection with an honest baseline: **Hit@1 = 80.0%, Hit@3 = 100.0%, MRR = 0.8944**, and highlighted that **abstention recall (50.0%)** is the primary weakness of the dense retriever.

2. **Automated CI/CD Quality Gates**:
   - Added `.github/workflows/ci.yml` running linting (`ruff`), test suite with coverage (`pytest`), offline RAG benchmark, frontend bundle compilation, and Docker build verification on every pull request.
   - Quality gate requires `Hit@3 >= 80%` and `MRR >= 0.75` without requiring external API keys.
   - Dependabot enabled for automated weekly dependency security bumps.

3. **Production Hardening**:
   - Enforced PDF magic-byte validation (`%PDF-`) and maximum file size caps (25 MB default) before disk or parser consumption.
   - Sanitized upload filenames with regex to defend against directory traversal attacks.
   - Integrated `slowapi` rate limiting (120 req/min general, 15 req/min uploads, 45 req/min LLM endpoints).
   - Structured JSON error responses and request logging with latency tracing in milliseconds.
   - Migrated application configuration to `pydantic-settings` (`AppSettings`) with `.env` file support.

4. **Containerization & Orchestration**:
   - Production Dockerfile for FastAPI backend running under a dedicated non-root user.
   - Multi-stage Dockerfile for React frontend served via Nginx with single-page application (SPA) client-side routing.
   - Unified `docker-compose.yml` for local orchestration with automated health checks.

5. **Repository & Documentation Polish**:
   - Complete rewrite of `README.md` with verified quickstart instructions, Mermaid architecture diagrams, honest metric tables, and clear trade-off explanations.
   - Standardized community files: `CONTRIBUTING.md`, `LICENSE` (MIT), PR and Issue templates.
   - Neutralized UI documentation, eliminating legacy references to external design systems.

---

## Detailed Changes

### 1. RAG Evaluation Harness v2

| Metric | Dev Set (36 queries) | Held-Out Test Set (36 queries) | 95% Wilson CI (Test) | CI Gate Target |
| :--- | :---: | :---: | :---: | :---: |
| **Hit@1** | 86.7% | **80.0%** (24/30) | [62.7%, 90.5%] | $\ge 70.0\%$ |
| **Hit@3** | 93.3% | **100.0%** (30/30) | [88.6%, 100.0%] | $\ge 80.0\%$ |
| **Hit@5** | 93.3% | **100.0%** (30/30) | [88.6%, 100.0%] | $\ge 85.0\%$ |
| **MRR** | 0.8944 | **0.8944** (26.8333/30) | exact | $\ge 0.75$ |
| **Abstention Recall** | 83.3% | **50.0%** (3/6) | [18.8%, 81.2%] | $\ge 45.0\%$ |
| **Abstention Precision**| 100.0%| **100.0%** (3/3) | [43.9%, 100.0%] | baseline |
| **False-Answer Rate** | 16.7% | **50.0%** (3/6) | [18.8%, 81.2%] | $\le 55.0\%$ |
| **Avg Retrieval Latency** | 693.57 ms | **653.48 ms** | — | $< 700\text{ ms}$ |

#### Key Evaluation Findings & Disclosures
- **Abstention Vulnerability:** Dense vector embeddings alone struggle with near-domain unanswerable queries. When an unanswerable query shares vocabulary with indexed documents (e.g. "quantum packet routing in IPv7" sharing terms with networking protocols), its cosine similarity exceeds the $\tau = 0.25$ threshold, producing a false answer instead of abstaining.
- **MRR Arithmetic Coincidence:** Dev and Test sets produced identical MRR scores of 0.8944. Detailed per-query inspection in `per_query_results.json` confirmed this was an exact mathematical coincidence: both reciprocal rank sums equal $\frac{161}{6} \approx 26.8333$ across 30 answerable queries.
- **Limitations:** All documents and questions are synthetic and AI-authored. The benchmark tests retrieval accuracy only, not downstream LLM generation quality. The held-out test set is no longer strictly untouched following per-query failure case study analysis.

### 2. Testing Suite
- Converted all tests to standard `pytest` framework with `pytest-asyncio`.
- Added unit tests for:
  - `test_pdf_service.py`: PDF extraction, page indexing, metadata parsing.
  - `test_vector_service.py`: Document ingestion, chunking, similarity retrieval.
  - `test_rag_service.py`: Prompt assembly, citation generation, provider fallback.
  - `test_auth_service.py`: Password hashing, token validation, user permissions.
  - `test_hardening.py`: Magic bytes, rate limiting, filename sanitisation.
- Overall backend test coverage: **78%** verified via `pytest-cov`.

### 3. Production Hardening
- Enforced input validation in FastAPI routes via Pydantic schemas.
- Configured CORS middleware using environment-defined `ALLOWED_ORIGINS`.
- Added structured request logging with timing headers to aid performance debugging.
- Fixed ChromaDB EphemeralClient lifecycle to maintain in-memory indexes reliably during benchmark runs.

---

## Upgrade Guide (v1.0.0 to v1.1.0)

1. **Environment Variables**:
   Review `.env.example`. The following optional variables have been formalized:
   - `ALLOWED_ORIGINS` (comma-separated list of permitted origins)
   - `MAX_UPLOAD_SIZE_MB` (default: 25)
   - `RATE_LIMIT_PER_MINUTE` (default: 60)
   - `LOG_LEVEL` (default: INFO)

2. **Docker Deployment**:
   ```bash
   docker compose down
   docker compose up --build -d
   ```

3. **Running Quality Checks Locally**:
   ```bash
   # Install updated dependencies
   pip install -r backend/requirements.txt
   
   # Run tests
   pytest backend/tests --cov=backend/app
   
   # Run RAG benchmark
   cd backend && python -m eval.run
   ```

---

## Known Limitations & Roadmap

- **Dense-Only Retrieval:** Currently relies exclusively on cosine similarity. BM25 sparse keyword search with Reciprocal Rank Fusion (RRF) is planned to resolve cross-document distractor confusion.
- **Table Linearity:** Standard text extraction flattens PDF tables into raw text strings. Layout-aware or markdown table extraction is slated for v1.2.0.
- **Query Expansion:** Multi-page synthesis queries currently miss secondary pages. Multi-query decomposition will be evaluated in the next release.
