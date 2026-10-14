# AI Identity & Digital Trust Automation Platform

[![CI/CD Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com/)
[![Flutter](https://img.shields.io/badge/Flutter-3.47%2B-02569B)](https://flutter.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL%2015%2B-3ECF8E)](https://supabase.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An explainable, privacy-first, modular platform that evaluates identity-related claims, digital documents, organization credentials, and autonomous AI-agent authorizations.

The platform issues four contextual, policy-driven decisions:
- **`ALLOW`** — The requested action satisfies the applicable policy.
- **`VERIFY`** — Additional evidence, step-up verification, or human review is required.
- **`RESTRICT`** — Only limited, explicitly scoped, least-privilege access is permitted.
- **`BLOCK`** — The requested action is denied under the current policy.

---

## 1. Monorepo Structure

```
ai-identity-and-digital-automation/
├── docs/                     # Roadmap, architecture, requirements & standards
│   ├── roadmap.md            # Master Project Roadmap (Phases 0–20)
│   ├── PROJECT_CURRENT_STATE.md # Baseline audit of existing components
│   ├── requirements_and_scope.md # Phase 1 Requirements & Scope Specification
│   ├── system_architecture.md   # Phase 2 C4 Architecture & Technical Design
│   └── git_conventions.md       # Git branching, commit conventions & security rules
├── frontend/                 # Flutter Web Application (Material 3)
│   ├── lib/                  # Screens 001–027, Core, Theme, Routing
│   ├── test/                 # Flutter widget & unit tests
│   ├── pubspec.yaml          # Flutter dependencies
│   └── .env.example          # Safe client-side environment template
├── backend/                  # FastAPI REST Microservice
│   ├── app/                  # Core, API v1, Schemas, Services (Policy Engine)
│   ├── requirements.txt      # Python dependencies
│   ├── pyproject.toml        # Ruff linting & pytest configuration
│   └── .env.example          # Server-side environment template
├── database/                 # Supabase PostgreSQL DDL & Migrations
│   ├── migrations/           # Versioned SQL migrations with RLS policies
│   ├── seed.sql              # Seed data for local development
│   └── README.md             # Supabase migration execution instructions
├── ai/                       # AI, OCR & Synthetic Data Assets
│   ├── synthetic_data/       # Specimen schemas (National ID, DL, Passport)
│   └── README.md             # Watermarking rules & synthetic data policies
├── tests/                    # End-to-end and integration tests
│   └── backend/              # Automated health, security, and policy tests
├── .gitignore                # Root gitignore blocking all secrets & build artifacts
└── .env.example              # Root environment template
```

---

## 2. Quick Start Guide

### Prerequisites
- Python 3.11+
- Flutter SDK 3.47+
- Git

### Backend Setup & Test Execution
```bash
# Navigate to backend and run tests
cd "ai identity and digital automation"
python -m pytest tests/backend -v
```

### Frontend Setup & Analyze
```bash
cd frontend
flutter pub get
flutter analyze
flutter test
```

---

## 3. Security & Zero Secret Guarantee
- **Never expose `SUPABASE_SERVICE_ROLE_KEY` to client builds:** The `service_role` key resides exclusively on the backend server.
- **PostgreSQL Row-Level Security:** Enforced on 100% of tables containing user records.
- **Synthetic Documents:** Only synthetic, watermarked identity documents are permitted during development and automated testing.
