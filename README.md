<div align="center">

# 🚀 AERAE Accelerator

### _AI-Powered Policy Analysis Platform with Multi-Provider LLM Support_

<br>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-SQLModel-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlmodel.tiangolo.com)
[![Azure OpenAI](https://img.shields.io/badge/Azure_OpenAI-EPAM_DIAL-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)](https://azure.microsoft.com)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.0_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Poetry](https://img.shields.io/badge/Poetry-Managed-60A5FA?style=for-the-badge&logo=poetry&logoColor=white)](https://python-poetry.org)
[![Tests](https://img.shields.io/badge/Tests-6_Passing-22C55E?style=for-the-badge&logo=pytest&logoColor=white)](#-running-tests)

<br>

</div>

---

<details open>
<summary><b>📑 Table of Contents</b></summary>

&nbsp;&nbsp;[📖 Overview](#-overview)
&nbsp;&nbsp;[✨ Key Features](#-key-features)
&nbsp;&nbsp;[🏗️ Architecture Flow](#️-architecture-flow)
&nbsp;&nbsp;[📁 Repository Structure](#-repository-structure)
&nbsp;&nbsp;[📄 File Descriptions](#-file-descriptions)
&nbsp;&nbsp;[🔌 API Endpoints](#-api-endpoints)
&nbsp;&nbsp;[⚙️ Getting Started](#️-getting-started)
&nbsp;&nbsp;[🔐 Environment Variables](#-environment-variables)
&nbsp;&nbsp;[🧰 Tech Stack](#-tech-stack)
&nbsp;&nbsp;[📜 License](#-license)

</details>

---

## 📖 Overview

**AERAE Accelerator** is a Python monorepo that provides a FastAPI backend capable of generating AI-powered content using **Google Gemini** and **Azure OpenAI** (via EPAM DIAL proxy). It features an intelligent **automatic fallback mechanism** — if Gemini is unavailable (rate-limited, quota exhausted, etc.), the system seamlessly switches to Azure OpenAI, ensuring uninterrupted service.

> [!NOTE]
> The platform is designed for **zero-downtime AI inference** — if one provider goes down, the other takes over automatically.

---

## ✨ Key Features

| | Feature | Description |
|:-:|:--------|:------------|
| 🔄 | **Multi-Provider AI** | Gemini + Azure OpenAI with automatic failover |
| ⚡ | **FastAPI** | High-performance async Python API |
| 🗄️ | **SQLModel + SQLite** | Lightweight database with auto table creation |
| 🔒 | **Secure Config** | Secrets loaded from git-ignored `.env` file |
| 🧪 | **Fully Tested** | 6 pytest test cases with mocked providers |
| 📦 | **Poetry** | Modern Python dependency management |
| 🔍 | **ChromaDB** | Vector store ready for RAG pipelines |
| 🛡️ | **Type-Safe** | Pydantic models for all request/response schemas |

---

## 🏗️ Architecture Flow

```mermaid
flowchart TD
    classDef clientStyle fill:#1e293b,stroke:#60a5fa,stroke-width:2px,color:#f8fafc
    classDef routerStyle fill:#0f766e,stroke:#2dd4bf,stroke-width:2px,color:#f8fafc
    classDef geminiStyle fill:#1e40af,stroke:#60a5fa,stroke-width:2px,color:#f8fafc
    classDef azureStyle fill:#7c3aed,stroke:#a78bfa,stroke-width:2px,color:#f8fafc
    classDef successStyle fill:#15803d,stroke:#4ade80,stroke-width:2px,color:#f8fafc
    classDef errorStyle fill:#b91c1c,stroke:#f87171,stroke-width:2px,color:#f8fafc
    classDef decisionStyle fill:#92400e,stroke:#fbbf24,stroke-width:2px,color:#f8fafc

    A["🌐 Client Request<br><code>POST /api/v1/generate</code>"]:::clientStyle
    B["⚡ FastAPI Router<br><code>routes.py</code>"]:::routerStyle
    C["🤖 Try Gemini First<br><code>gemini_service.py</code>"]:::geminiStyle
    D{{"✅ Gemini<br>Success?"}}:::decisionStyle
    E["✅ Return Response<br><code>source: gemini</code>"]:::successStyle
    F["☁️ Fallback → Azure OpenAI<br><code>azure_openai_service.py</code>"]:::azureStyle
    G{{"✅ Azure<br>Success?"}}:::decisionStyle
    H["✅ Return Response<br><code>source: azure-openai</code><br><code>fallback: true</code>"]:::successStyle
    I["❌ 502 Error<br>Both Providers Failed"]:::errorStyle

    A --> B
    B --> C
    C --> D
    D -- "✅ Yes" --> E
    D -- "❌ No (429 / Error)" --> F
    F --> G
    G -- "✅ Yes" --> H
    G -- "❌ No" --> I
```

---

## 📁 Repository Structure

<details open>
<summary><b>Click to expand / collapse</b></summary>

```
aerae-accelerator/
│
├── 📄 .env.example              # 🔑 Environment variable template (safe to commit)
├── 🔒 .env                      # 🚫 Real secrets (git-ignored)
├── 📄 .gitignore                # 🛡️ Ignore rules for Python, Node.js, IDE, Infra
│
├── 🔧 backend/                  # ── FastAPI Backend ─────────────────────────
│   ├── 📄 pyproject.toml        #    Poetry dependencies & project config
│   │
│   ├── 📂 app/                  #    Application source code
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py           #    ⚡ FastAPI entry point & lifespan events
│   │   │
│   │   ├── 📂 core/             #    🔩 Core configuration & infrastructure
│   │   │   ├── 📄 config.py     #       Pydantic Settings (loads .env)
│   │   │   └── 📄 db.py         #       SQLModel engine & table creation
│   │   │
│   │   ├── 📂 api/              #    🌐 API layer (routes & schemas)
│   │   │   └── 📄 routes.py     #       All API endpoints & Pydantic schemas
│   │   │
│   │   └── 📂 services/         #    🤖 Business logic & LLM integrations
│   │       ├── 📄 gemini_service.py        # Google Gemini SDK wrapper
│   │       └── 📄 azure_openai_service.py  # Azure OpenAI SDK wrapper
│   │
│   └── 📂 tests/                #    🧪 Pytest test suite
│       ├── 📄 test_setup.py     #       Environment verification test
│       └── 📄 test_main.py      #       6 test cases (health, generate, fallback)
│
├── 📂 frontend/                 # 🎨 Frontend application (placeholder)
├── 📂 infra/                    # ☁️  Infrastructure-as-Code (placeholder)
└── 📂 policies/                 # 📋 Policy documents (placeholder)
```

</details>

---

## 📄 File Descriptions

<details>
<summary><b>🏠 Root Level</b></summary>

| File | Description |
|:-----|:------------|
| `.env.example` | Template with all required environment variables and placeholder values. Copy to `.env` and fill in real keys. |
| `.env` | **Git-ignored.** Holds actual API keys and secrets locally. Never committed to the repository. |
| `.gitignore` | Comprehensive ignore rules covering Python, Node.js, IDE files, Terraform state, and secrets. |

</details>

<details>
<summary><b>🔩 Backend — Core</b></summary>

| File | Description |
|:-----|:------------|
| `backend/pyproject.toml` | Poetry project config — declares dependencies (FastAPI, uvicorn, SQLModel, google-genai, openai, chromadb, pydantic-settings) and dev tools (pytest, httpx, ruff). |
| `backend/app/main.py` | **FastAPI app entry point.** Initializes the app, registers the API router under `/api/v1`, sets up a lifespan handler that auto-creates database tables on startup, and exposes a `/health` liveness probe. |
| `backend/app/core/config.py` | **Pydantic Settings class.** Securely loads all environment variables from the root-level `.env` file. Manages keys for Azure OpenAI, Gemini, database URL, ChromaDB path, and app settings. |
| `backend/app/core/db.py` | **Database engine.** Creates a SQLModel/SQLAlchemy engine connected to SQLite (`aerae_local.db`). Provides `create_db_and_tables()` called at startup to auto-create all registered model tables. |

</details>

<details>
<summary><b>🌐 Backend — API</b></summary>

| File | Description |
|:-----|:------------|
| `backend/app/api/routes.py` | **All API endpoints.** Defines request/response Pydantic schemas (`PromptRequest`, `GenerateResponse`) and four routes: unified `/generate` with fallback logic, direct `/generate/gemini`, direct `/generate/azure-openai`, and a root `/` info endpoint. |

</details>

<details>
<summary><b>🤖 Backend — Services</b></summary>

| File | Description |
|:-----|:------------|
| `backend/app/services/gemini_service.py` | **Google Gemini wrapper.** Initializes a `genai.Client` with the API key and exposes `generate_content(prompt)` using the `gemini-2.0-flash-lite` model. |
| `backend/app/services/azure_openai_service.py` | **Azure OpenAI wrapper.** Initializes an `AzureOpenAI` client pointed at the EPAM DIAL proxy and exposes `chat_completion(prompt)` using the `gpt-4o-mini-2024-07-18` deployment. |

</details>

<details>
<summary><b>🧪 Backend — Tests</b></summary>

| File | Description |
|:-----|:------------|
| `backend/tests/test_setup.py` | **Environment verification.** Single `assert True` test to confirm pytest is working. |
| `backend/tests/test_main.py` | **Pytest test suite (6 tests).** Covers: health check, unified generate (Gemini success), unified generate (Gemini fail → Azure fallback), unified generate (both fail → 502), direct Gemini endpoint, and direct Azure OpenAI endpoint. All LLM calls are mocked. |

</details>

---

## 🔌 API Endpoints

### 💚 Health Check

| Method | Path | Description |
|:------:|:-----|:------------|
| ![GET](https://img.shields.io/badge/GET-22C55E?style=flat-square) | `/health` | Liveness probe — returns `{"status": "ok"}` |

### 🤖 Content Generation

| Method | Path | Description |
|:------:|:-----|:------------|
| ![POST](https://img.shields.io/badge/POST-3B82F6?style=flat-square) | `/api/v1/generate` | **Unified endpoint** — Tries Gemini first, auto-falls back to Azure OpenAI on failure |
| ![POST](https://img.shields.io/badge/POST-3B82F6?style=flat-square) | `/api/v1/generate/gemini` | Direct call to Google Gemini only (no fallback) |
| ![POST](https://img.shields.io/badge/POST-3B82F6?style=flat-square) | `/api/v1/generate/azure-openai` | Direct call to Azure OpenAI only (no fallback) |
| ![GET](https://img.shields.io/badge/GET-22C55E?style=flat-square) | `/api/v1/` | API version info |

<details>
<summary><b>📥 Request / Response Examples</b></summary>

#### Request Body (POST endpoints)

```json
{
  "prompt": "Explain how AI works in a few words",
  "model": "gemini-2.0-flash-lite"          // optional — uses default if omitted
}
```

#### Response Body

```json
{
  "source": "gemini",                   // "gemini" or "azure-openai"
  "model": "gemini-2.0-flash-lite",
  "response": "AI learns patterns from data to make predictions.",
  "fallback_used": false,               // true if Azure was used as fallback
  "fallback_reason": null               // explains why fallback was triggered
}
```

</details>

<details>
<summary><b>🖥️ cURL Examples</b></summary>

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

</details>

---

## ⚙️ Getting Started

### 📋 Prerequisites

> [!IMPORTANT]
> Make sure you have the following installed before proceeding.

- **Python 3.11+** — [Download](https://python.org/downloads)
- **Poetry** — [Install Guide](https://python-poetry.org/docs/#installation)

### 1️⃣ Clone & Configure

```bash
git clone <repo-url> aerae-accelerator
cd aerae-accelerator

# Create your local .env from the template
cp .env.example .env
# ✏️ Edit .env and fill in your real API keys
```

### 2️⃣ Install Dependencies

```bash
cd backend
poetry install        # installs main + dev dependencies
```

### 3️⃣ Run the Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

> [!TIP]
> 🌐 API live at **http://127.0.0.1:8000**
> 📚 Interactive docs at **http://127.0.0.1:8000/docs**

### 4️⃣ Running Tests

```bash
cd backend
pytest -v
```

---

## 🔐 Environment Variables

> [!CAUTION]
> Never commit your `.env` file. Use `.env.example` as a template and keep real keys local.

| Variable | Required | Default | Description |
|:---------|:--------:|:--------|:------------|
| `APP_NAME` | | `AERAE Accelerator` | Application display name |
| `API_V1_STR` | | `/api/v1` | API version prefix |
| `DEBUG` | | `False` | Enable debug mode & SQL echo |
| `DATABASE_URL` | | `sqlite:///./aerae_local.db` | SQLModel database connection string |
| `AZURE_OPENAI_API_KEY` | ✅ | — | Azure OpenAI / EPAM DIAL API key |
| `AZURE_OPENAI_ENDPOINT` | | `https://ai-proxy.lab.epam.com` | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_VERSION` | | `2024-02-01` | Azure OpenAI API version |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | | `gpt-4o-mini-2024-07-18` | Azure deployment model name |
| `GEMINI_API_KEY` | ✅ | — | Google Gemini API key |
| `CHROMA_PERSIST_DIRECTORY` | | `./chroma_data` | ChromaDB vector store path |

---

## 🧰 Tech Stack

<div align="center">

| Layer | Technology | Badge |
|:------|:-----------|:------|
| **API Framework** | FastAPI 0.115+ | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) |
| **Server** | Uvicorn (ASGI) | ![Uvicorn](https://img.shields.io/badge/Uvicorn-2D3748?style=flat-square&logo=gunicorn&logoColor=white) |
| **Database** | SQLite via SQLModel | ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) |
| **Vector Store** | ChromaDB | ![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=flat-square&logo=databricks&logoColor=white) |
| **LLM Provider 1** | Google Gemini | ![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=flat-square&logo=google&logoColor=white) |
| **LLM Provider 2** | Azure OpenAI (EPAM DIAL) | ![Azure](https://img.shields.io/badge/Azure_OpenAI-0078D4?style=flat-square&logo=microsoftazure&logoColor=white) |
| **Config** | Pydantic Settings | ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white) |
| **Testing** | Pytest + HTTPX | ![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white) |
| **Linting** | Ruff | ![Ruff](https://img.shields.io/badge/Ruff-D7FF64?style=flat-square&logo=ruff&logoColor=black) |
| **Dependency Mgmt** | Poetry | ![Poetry](https://img.shields.io/badge/Poetry-60A5FA?style=flat-square&logo=poetry&logoColor=white) |

</div>

---

<div align="center">

**Built with ❤️ by the AERAE Team**

[![Website](https://img.shields.io/badge/Website-thedataarch.com-0A66C2?style=for-the-badge&logo=google-chrome&logoColor=white)](https://thedataarch.com/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-nsharma02-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/nsharma02/)

</div>
