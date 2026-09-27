# Contributing to OpenJustice Backend

Thank you for your interest in contributing to OpenJustice! This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create a branch** for your changes
4. **Make your changes** and test them
5. **Submit a Pull Request**

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- PostgreSQL 15+ with the `pgvector` extension

### Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/OpenJustice-Backend-Repo.git
cd OpenJustice-Backend-Repo

# Create environment file
cp .env.example .env
# Edit .env with your local settings (database URL, API keys, etc.)

# Install dependencies
uv sync

# Set PYTHONPATH
# Windows PowerShell:
$env:PYTHONPATH = (Get-Location).Path
# macOS/Linux:
export PYTHONPATH="$(pwd)"

# Initialize database
uv run python -m app.infrastructure.db.init_db

# Run migrations
uv run alembic upgrade head

# Start the server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html
```

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feat/add-document-search` — New features
- `fix/websocket-reconnection` — Bug fixes
- `docs/update-api-reference` — Documentation updates
- `refactor/simplify-rag-pipeline` — Code refactoring

### Architecture Guidelines

This project follows **Clean Architecture** with four layers. Please respect the dependency direction (outer → inner):

1. **Domain** — Entities, interfaces (ports), exceptions. No external dependencies.
2. **Application** — Services, DTOs, prompts. Depends only on Domain.
3. **Infrastructure** — Repositories, external clients, security. Implements Domain interfaces.
4. **Presentation** — Controllers, schemas, middleware. Orchestrates Application services.

> **Rule:** Inner layers must never import from outer layers. Use dependency injection via interfaces.

### Commit Messages

Write clear, concise commit messages:

```
feat: add semantic search for Tamil legal documents
fix: prevent duplicate WebSocket connections on reconnect
docs: add API rate limiting documentation
test: add unit tests for voice transcription service
```

## Pull Request Process

1. **Update your branch** with the latest `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
2. **Ensure all tests pass**: `uv run pytest tests/ -v`
3. **Format your code**: `uv run black .` and `uv run isort .`
4. **Lint your code**: `uv run flake8 .`
5. **Write a clear PR description** explaining:
   - What the change does
   - Why it's needed
   - How it was tested
6. **Link related issues** if applicable

### PR Review Criteria

- Code follows the project's architecture and coding standards
- Tests are included for new functionality
- No hardcoded secrets or credentials
- Documentation is updated where relevant
- The PR is focused — one feature or fix per PR

## Coding Standards

- **Formatter**: Black (line length: 88)
- **Import Sorting**: isort
- **Linting**: Flake8
- **Type Checking**: mypy
- **Docstrings**: Use triple-quoted docstrings for all public functions and classes

## Reporting Bugs

When reporting bugs, please include:

1. **Description**: What happened vs. what you expected
2. **Steps to Reproduce**: Minimal steps to trigger the bug
3. **Environment**: OS, Python version, database version
4. **Logs/Screenshots**: Any relevant error output

Use the [GitHub Issues](https://github.com/shashinherath/OpenJustice-Backend-Repo/issues) page to report bugs.

## Suggesting Features

Feature suggestions are welcome! Please open a [GitHub Issue](https://github.com/shashinherath/OpenJustice-Backend-Repo/issues) with:

1. **Problem**: What problem does the feature solve?
2. **Proposed Solution**: How should it work?
3. **Alternatives Considered**: Any other approaches you thought about?

---

Thank you for helping make OpenJustice better! ⚖️
