# Contributing to AI Study Assistant

Thank you for contributing to **AI Study Assistant**! We welcome bug reports, feature requests, documentation improvements, and code contributions.

---

## Getting Started

### 1. Prerequisites
- **Python:** 3.11+
- **Node.js:** 20+
- **Git**
- **Docker & Docker Compose** (optional, for containerised testing)
- **Ollama** (optional, for local embedding and LLM generation)

### 2. Fork & Clone
```bash
git clone https://github.com/[Your-Username]/study-assistant.git
cd study-assistant
```

### 3. Local Environment Setup

#### Backend:
```bash
cd backend
python -m venv venv

# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

#### Frontend:
```bash
cd frontend
npm ci
```

---

## Development Workflow

### Branch Naming Conventions
- `feat/feature-name` — new features or capabilities
- `fix/bug-description` — defect fixes
- `test/test-suite` — test additions or improvements
- `docs/doc-update` — documentation updates
- `chore/task-name` — tooling, dependencies, or configuration

### Commit Messages
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
```text
feat(quiz): add timer and difficulty selection
fix(pdf): handle password-protected documents gracefully
test(rag): add golden retrieval test cases
docs(readme): update docker compose instructions
```

---

## Testing & Quality Checks

Run the following checks before opening a Pull Request:

```bash
# 1. Run Ruff linter and format check
python -m ruff check .
python -m ruff format --check .

# 2. Run Pytest suite with coverage
pytest backend/tests --cov=backend/app --cov-report=term-missing

# 3. Run Offline RAG Evaluation Benchmark (from backend/ directory)
cd backend
python -m eval.run

# 4. Validate Frontend Build
cd frontend
npm run build
```

---

## Submitting a Pull Request

1. Push your branch to your fork.
2. Open a Pull Request targeting the `main` branch.
3. Fill out the PR template completely.
4. Ensure all CI checks pass.
5. Address any code review comments.
