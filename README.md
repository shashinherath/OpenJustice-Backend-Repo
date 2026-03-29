# OpenJustice Backend

An AI-powered legal assistance platform backend built with FastAPI, PostgreSQL (`pgvector`), and Clean Architecture.

## 🚀 Overview

OpenJustice Backend serves as the brain for an interactive legal assistant. It leverages RAG (Retrieval-Augmented Generation) patterns to provide legally grounded answers, multilingual translation, document summarization, and incorporates advanced features like WhatsApp integration and Voice (Speech-to-Text & Text-to-Speech).

## 🧰 Tech Stack

- **Framework**: FastAPI (Python 3.10+)
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Database**: PostgreSQL with `pgvector` for vector similarity search
- **ORM**: SQLAlchemy (Async)
- **Validation & Settings**: Pydantic & Pydantic-Settings
- **Security**: JWT (`python-jose`) and `bcrypt` password hashing
- **AI / NLP**: OpenAI (GPT-4o), LangChain, Hugging Face Transformers
- **Voice / Speech**: OpenAI Whisper

## 🏗️ Architecture

The codebase adheres strictly to **Clean Architecture** patterns, promoting separation of concerns and maintainability across four primary layers:
1. **Domain**: Core business entities and abstract interfaces.
2. **Application**: Use cases, business logic, DTOs, and application services.
3. **Infrastructure**: Database connections, external API adapters, repositories, security handlers.
4. **Presentation**: FastAPI endpoints (Controllers), Middlewares, Schemas.

## ⚙️ Local Development Setup

### 1. Prerequisites
- **Python 3.10+**
- **uv** installed (`pip install uv` or `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`)
- **PostgreSQL 15+** with the **`pgvector`** extension installed on your system. *(If using Docker: `docker run -d --name pgvector-db -e POSTGRES_PASSWORD=postgres -p 5432:5432 pgvector/pgvector:16`)*

### 2. Configure Environment
Copy the example environment parameters to a new `.env` file and fill out the necessary AI API Keys and Database credentials.
```bash
cp .env.example .env
```

### 3. Install Dependencies
Synchronize your virtual environment locally. `uv` will automatically create the `.venv` and install the locked dependencies.
```bash
uv sync
```

### 4. Initialize Database
Create all tables and activate the `vector` extension by running the initial DB setup script (ensure your PostgreSQL is active).
```bash
uv run python -m app.infrastructure.db.init_db
```

### 5. Run the Server
Launch the FastAPI development server with hot-reloading:
```bash
uv run uvicorn app.main:app --reload
```

You can now visit the interactive API documentation at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 🧪 Testing
The repository utilizes `pytest` with async support. Execute tests using:
```bash
uv run pytest
```
