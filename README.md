# LoanFlow AI

**Autonomous AI-Powered Mortgage Document Processing and Underwriting Assistant**

LoanFlow AI streamlines and accelerates mortgage origination by automating the ingestion, extraction, cross-verification, and underwriting risk analysis of complex borrower financial packages.

---

## 🌟 Key Features

- **Multi-Format Document Ingestion**: Ingest PDF packages, scanned forms, and images (W-2s, Form 1040s, pay stubs, bank statements).
- **Hybrid Extraction Engine**: Fast digital text extraction via PyMuPDF with automatic fallback to high-accuracy OCR for scanned documents.
- **LangGraph Underwriting Agent**: State machine-driven verification workflows:
  - Document Classification & Identification
  - Key Entity & Financial Data Extraction
  - Cross-Document Reconciliation (e.g., verifying pay stub earnings against W-2 box 1 and tax returns)
  - Debt-to-Income (DTI) & Underwriting Guideline Calculations
- **Privacy-First Local LLM Support**: Native support for Ollama (Llama 3.1, Mistral, Qwen) ensuring sensitive borrower PII never leaves the local/on-premise boundary.
- **Auditable Decision Engine**: Full traceability of agent reasoning steps, flag triggers, and rule evaluations stored in PostgreSQL.
- **Modern Loan Officer Workspace**: Clean React + TypeScript interface for review queues, side-by-side document inspection, and underwriting sign-offs.

---

## 🏗️ Architecture Overview

```text
                      ┌──────────────────────────────────────┐
                      │    React + TypeScript Frontend       │
                      │   (Document Queue & Underwriting UI) │
                      └──────────────────┬───────────────────┘
                                         │ REST / WebSocket
                                         ▼
                      ┌──────────────────────────────────────┐
                      │       FastAPI Backend Service        │
                      └──────────┬─────────────────┬─────────┘
                                 │                 │
            ┌────────────────────┴────────┐        └────────────────────┐
            ▼                             ▼                             ▼
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│  Extraction Engine   │      │  LangGraph Workflow  │      │ PostgreSQL Database  │
│  - PyMuPDF (Digital) │      │  - Document Classify │      │ - Applications       │
│  - OCR (Scanned/Img) │      │  - Cross-Verify Data │      │ - Extracted Entities │
└──────────────────────┘      │  - Underwrite & DTI  │      │ - Audit Logs & Flags │
                              └──────────┬───────────┘      └──────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  Ollama (Local LLM)  │
                              │  - Llama 3.1/Mistral │
                              └──────────────────────┘
```

---

## 📁 Project Structure

```text
loanflow-ai/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI REST route handlers
│   │   ├── core/            # Config, security, and logging
│   │   ├── database/        # Async SQLAlchemy models & engine
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── services/        # PyMuPDF, OCR, and LangGraph agent logic
│   ├── tests/               # Backend pytest test suite
│   ├── uploads/             # Secure local document staging (.gitignored)
│   ├── requirements.txt     # Backend Python dependencies
│   └── .env.example         # Environment template
├── frontend/                # React + TypeScript frontend application
├── docker-compose.yml       # Local PostgreSQL and service orchestration
├── .gitignore               # Multi-tier gitignore
└── README.md                # Project documentation
```

---

## 🛠️ Prerequisites

- **Python**: 3.12 (recommended for LangGraph & PyMuPDF stability)
- **Node.js**: v20+ / v24+ & npm
- **Docker & Docker Desktop**: For PostgreSQL service
- **Ollama**: For local LLM inference

---

## 🚀 Quickstart Guide

### 1. Database Setup
```bash
docker compose up -d
```
*(PostgreSQL with pgvector starts on port **5433** to avoid conflicts with native PostgreSQL)*

### 2. Backend Setup
```bash
cd backend

# Apply database migrations
python migrate.py upgrade head

# (Optional) Seed realistic demo applications and mortgage documents
python seed_demo.py

# Start the FastAPI server
python -m uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: `http://localhost:8000/api/v1/docs`
- Health check: `http://localhost:8000/api/v1/health`

### 3. Frontend Dashboard Setup
```bash
cd frontend
npm install
npm run dev
```
- Open in browser: `http://localhost:5173`

---

## 🧪 Testing Suite

Run the full automated test suite (18 unit & integration tests covering models, CRUD, PyMuPDF extraction, and LangGraph underwriting):
```bash
cd backend
python -m pytest
```

---

## 📊 Underwriting Decision Matrix & Conforming Rules

| Metric / Rule | Conforming Benchmark | Agent Action |
| :--- | :--- | :--- |
| **Back-End DTI** | $\le 43.0\%$ | Passes Fannie Mae conforming debt threshold |
| **Back-End DTI** | $43.1\% - 50.0\%$ | `REFER_TO_HUMAN` (Requires underwriter exception review & compensating factors) |
| **Back-End DTI** | $> 50.0\%$ | `REJECTED` (Excessive debt burden exceeds secondary market ceiling) |
| **Front-End Housing Ratio** | $\le 28.0\%$ | Passes housing expense ratio guidelines |
| **Cross-Doc Income Variance** | $\le 2.0\%$ | Reconciles W-2 Box 1 wages with Paystub annualized gross earnings |
| **Income Discrepancy** | $> 2.0\%$ | Emits `DiscrepancyFlag` & generates prior-to-close explanation condition |
| **Missing Documentation** | No W-2 / Paystub | `REFER_TO_HUMAN` with actionable document submission requirements |

---

## 🔒 Security & Privacy Notice
Mortgage documents contain sensitive Personally Identifiable Information (PII) and financial records. LoanFlow AI is designed with privacy-first principles: local file storage is gitignored, and agent inference is compatible with locally hosted Ollama models to prevent unauthorized external transmission.
