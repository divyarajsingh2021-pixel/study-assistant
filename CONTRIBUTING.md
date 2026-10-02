# Contributing to AI Study Assistant

Thank you for your interest in contributing to **AI Study Assistant**! We welcome bug reports, feature requests, documentation improvements, and code contributions.

---

## Code of Conduct

Please be respectful, collaborative, and constructive when engaging in issues and discussions.

---

## Getting Started

### 1. Prerequisites
- **Python:** 3.11+
- **Node.js:** 20+
- **Git**
- **Docker & Docker Compose** (Optional for container testing)

### 2. Fork & Clone
```bash
git clone https://github.com/your-username/study-assistant.git
cd study-assistant
```

### 3. Local Environment Setup

#### Backend Setup:
```bash
cd backend
python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

#### Frontend Setup:
```bash
cd frontend
npm ci
```

---

## Development Workflow

### Branch Naming Conventions
- `feat/feature-name` for new capabilities
- `fix/bug-description` for defect fixes
- `test/test-suite` for testing additions
- `docs/doc-update` for documentation changes
- `chore/task-name` for tooling and build updates

### Commit Messages
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
```
feat(quiz): add timer and difficulty selection
fix(pdf): handle password-protected documents gracefully
test(rag): add golden retrieval test cases
docs(readme): update docker compose instructions
```

---

## Testing & Quality Checks

Before submitting a Pull Request, make sure all tests pass and formatting is clean:

```bash
# 1. Run Ruff linter and formatter
ruff check .
ruff format --check .

# 2. Run Pytest test suite with coverage
pytest backend/tests --cov=backend/app --cov-report=term-missing

# 3. Run Offline RAG Evaluation Benchmark
python -m eval.run

# 4. Validate Frontend Build
cd frontend
npm run build
```

---

## Submitting a Pull Request

1. Push your branch to your fork.
2. Open a Pull Request targeting the `main` branch.
3. Ensure the PR title clearly describes the change.
4. Verify that all GitHub Actions CI checks pass.
5. Address any code review feedback.
