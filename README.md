<p align="center">
  <h1 align="center">🚀 AERAE Accelerator</h1>
  <p align="center">
    <strong>AI-powered policy analysis platform with multi-provider LLM support</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white" alt="FastAPI">
    <img src="https://img.shields.io/badge/SQLite-SQLModel-003B57?logo=sqlite&logoColor=white" alt="SQLite">
    <img src="https://img.shields.io/badge/Azure_OpenAI-EPAM_DIAL-0078D4?logo=microsoftazure&logoColor=white" alt="Azure OpenAI">
    <img src="https://img.shields.io/badge/Google_Gemini-2.0_Flash-4285F4?logo=google&logoColor=white" alt="Gemini">
  </p>
</p>

---

## 📖 Overview

**AERAE Accelerator** is a Python monorepo that provides a FastAPI backend capable of generating AI-powered content using **Google Gemini** and **Azure OpenAI** (via EPAM DIAL proxy). It features an intelligent **automatic fallback mechanism** — if Gemini is unavailable (rate-limited, quota exhausted, etc.), the system seamlessly switches to Azure OpenAI, ensuring uninterrupted service.

---

## ✨ Key Features

- 🔄 **Multi-provider AI** — Gemini + Azure OpenAI with automatic failover
- ⚡ **FastAPI** — High-performance async Python API
- 🗄️ **SQLModel + SQLite** — Lightweight database with auto table creation
- 🔒 **Secure config** — Secrets loaded from git-ignored `.env` file
- 🧪 **Fully tested** — 6 pytest test cases with mocked providers
- 📦 **Poetry** — Modern Python dependency management

---

## 🏗️ Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT REQUEST                           │
│              POST /api/v1/generate { prompt }                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │   FastAPI Router   │
                 │   (routes.py)      │
                 └────────┬──────────┘
                          │
                ┌─────────▼─────────┐
                │  Try Gemini First  │
                │  (gemini_service)  │
                └────────┬──────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
         ✅ Success            ❌ Failure (429/error)
              │                     │
              ▼                     ▼
     ┌────────────────┐   ┌─────────────────────┐
     │ Return response │   │ Fallback to Azure   │
     │ source: gemini  │   │ (azure_openai_svc)  │
     └────────────────┘   └──────────┬──────────┘
                                     │
                          ┌──────────┴──────────┐
                          │                     │
                     ✅ Success            ❌ Failure
                          │                     │
                          ▼                     ▼
                 ┌────────────────┐    ┌────────────────┐
                 │ Return response │    │  502 Error:    │
                 │ source: azure   │    │  Both failed   │
                 │ fallback: true  │    └────────────────┘
                 └────────────────┘
```

---

## 📁 Repository Structure

```
aerae-accelerator/
├── 📄 .env.example              # Environment variable template (safe to commit)
├── 🔒 .env                      # Real secrets (git-ignored)
├── 📄 .gitignore                # Ignore rules for Python, Node.js, IDE, Infra
│
├── 🔧 backend/                  # FastAPI backend application
│   ├── 📄 pyproject.toml        # Poetry dependencies & project config
│   │
│   ├── 📂 app/                  # Application source code
│   │   ├── 📄 __init__.py       # Package marker
│   │   ├── 📄 main.py           # FastAPI app entry point & lifespan events
│   │   │
│   │   ├── 📂 core/             # Core configuration & infrastructure
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 config.py     # Pydantic Settings (loads .env securely)
│   │   │   └── 📄 db.py         # SQLModel engine & table creation
│   │   │
│   │   ├── 📂 api/              # API layer (routes & schemas)
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 routes.py     # All API endpoints & Pydantic schemas
│   │   │
│   │   └── 📂 services/         # Business logic & external integrations
│   │       ├── 📄 __init__.py
│   │       ├── 📄 gemini_service.py        # Google Gemini SDK wrapper
│   │       └── 📄 azure_openai_service.py  # Azure OpenAI SDK wrapper
│   │
│   └── 📂 tests/                # Pytest test suite
│       ├── 📄 __init__.py
│       └── 📄 test_main.py      # 6 test cases (health, generate, fallback)
│
├── 📂 frontend/                 # Frontend application (placeholder)
├── 📂 infra/                    # Infrastructure-as-Code (placeholder)
└── 📂 policies/                 # Policy documents (placeholder)
```

---

## 📄 File Descriptions

### Root Level

| File | Description |
|:-----|:------------|
| `.env.example` | Template with all required environment variables and placeholder values. Copy to `.env` and fill in real keys. |
| `.env` | **Git-ignored.** Holds actual API keys and secrets locally. Never committed to the repository. |
| `.gitignore` | Comprehensive ignore rules covering Python, Node.js, IDE files, Terraform state, and secrets. |

### Backend — Core

| File | Description |
|:-----|:------------|
| `backend/pyproject.toml` | Poetry project config — declares dependencies (FastAPI, uvicorn, SQLModel, google-genai, openai, chromadb, pydantic-settings) and dev tools (pytest, httpx, ruff). |
| `backend/app/main.py` | **FastAPI app entry point.** Initializes the app, registers the API router under `/api/v1`, sets up a lifespan handler that auto-creates database tables on startup, and exposes a `/health` liveness probe. |
| `backend/app/core/config.py` | **Pydantic Settings class.** Securely loads all environment variables from the root-level `.env` file. Manages keys for Azure OpenAI, Gemini, database URL, ChromaDB path, and app settings. |
| `backend/app/core/db.py` | **Database engine.** Creates a SQLModel/SQLAlchemy engine connected to SQLite (`aerae_local.db`). Provides `create_db_and_tables()` called at startup to auto-create all registered model tables. |

### Backend — API

| File | Description |
|:-----|:------------|
| `backend/app/api/routes.py` | **All API endpoints.** Defines request/response Pydantic schemas (`PromptRequest`, `GenerateResponse`) and four routes: unified `/generate` with fallback logic, direct `/generate/gemini`, direct `/generate/azure-openai`, and a root `/` info endpoint. |

### Backend — Services

| File | Description |
|:-----|:------------|
| `backend/app/services/gemini_service.py` | **Google Gemini wrapper.** Initializes a `genai.Client` with the API key and exposes `generate_content(prompt)` using the `gemini-2.0-flash` model. |
| `backend/app/services/azure_openai_service.py` | **Azure OpenAI wrapper.** Initializes an `AzureOpenAI` client pointed at the EPAM DIAL proxy and exposes `chat_completion(prompt)` using the `gpt-4o-mini-2024-07-18` deployment. |

### Backend — Tests

| File | Description |
|:-----|:------------|
| `backend/tests/test_main.py` | **Pytest test suite (6 tests).** Covers: health check, unified generate (Gemini success), unified generate (Gemini fail → Azure fallback), unified generate (both fail → 502), direct Gemini endpoint, and direct Azure OpenAI endpoint. All LLM calls are mocked. |

---

## 🔌 API Endpoints

### Health Check

| Method | Path | Description |
|:------:|:-----|:------------|
| `GET` | `/health` | Liveness probe. Returns `{"status": "ok"}` |

### Content Generation

| Method | Path | Description |
|:------:|:-----|:------------|
| `POST` | `/api/v1/generate` | **Unified endpoint** — Tries Gemini first, auto-falls back to Azure OpenAI on failure |
| `POST` | `/api/v1/generate/gemini` | Direct call to Google Gemini only (no fallback) |
| `POST` | `/api/v1/generate/azure-openai` | Direct call to Azure OpenAI only (no fallback) |
| `GET` | `/api/v1/` | API version info |

### Request Body (POST endpoints)

```json
{
  "prompt": "Explain how AI works in a few words",
  "model": "gemini-2.0-flash"          // optional — uses default if omitted
}
```

### Response Body

```json
{
  "source": "gemini",                   // "gemini" or "azure-openai"
  "model": "gemini-2.0-flash",
  "response": "AI learns patterns from data to make predictions.",
  "fallback_used": false,               // true if Azure was used as fallback
  "fallback_reason": null               // explains why fallback was triggered
}
```

### Example — cURL

```bash
# Unified (auto-fallback)
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is machine learning?"}'

# Direct Gemini
curl -X POST http://localhost:8000/api/v1/generate/gemini \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is machine learning?"}'

# Direct Azure OpenAI
curl -X POST http://localhost:8000/api/v1/generate/azure-openai \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is machine learning?"}'

# Health check
curl http://localhost:8000/health
```

---

## ⚙️ Getting Started

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation) (recommended) or pip

### 1. Clone & Configure

```bash
git clone <repo-url> aerae-accelerator
cd aerae-accelerator

# Create your local .env from the template
cp .env.example .env
# Edit .env and fill in your real API keys
```

### 2. Install Dependencies

```bash
cd backend
poetry install        # or: pip install -e ".[dev]"
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is now live at **http://127.0.0.1:8000**
Interactive docs at **http://127.0.0.1:8000/docs**

### 4. Run Tests

```bash
cd backend
pytest -v
```

---

## 🔐 Environment Variables

| Variable | Required | Default | Description |
|:---------|:--------:|:--------|:------------|
| `APP_NAME` | No | `AERAE Accelerator` | Application display name |
| `API_V1_STR` | No | `/api/v1` | API version prefix |
| `DEBUG` | No | `False` | Enable debug mode & SQL echo |
| `DATABASE_URL` | No | `sqlite:///./aerae_local.db` | SQLModel database connection string |
| `AZURE_OPENAI_API_KEY` | Yes | — | Azure OpenAI / EPAM DIAL API key |
| `AZURE_OPENAI_ENDPOINT` | No | `https://ai-proxy.lab.epam.com` | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_VERSION` | No | `2024-02-01` | Azure OpenAI API version |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | No | `gpt-4o-mini-2024-07-18` | Azure deployment model name |
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `CHROMA_PERSIST_DIRECTORY` | No | `./chroma_data` | ChromaDB vector store path |

---

## 🧰 Tech Stack

| Layer | Technology |
|:------|:-----------|
| **API Framework** | FastAPI 0.115+ |
| **Server** | Uvicorn (ASGI) |
| **Database** | SQLite via SQLModel |
| **Vector Store** | ChromaDB |
| **LLM Provider 1** | Google Gemini (`google-genai`) |
| **LLM Provider 2** | Azure OpenAI (`openai` SDK, EPAM DIAL) |
| **Config** | Pydantic Settings |
| **Testing** | Pytest + HTTPX TestClient |
| **Linting** | Ruff |
| **Dependency Mgmt** | Poetry |

---

## 📜 License

Internal project — EPAM Systems.
