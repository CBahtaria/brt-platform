# BRT Platform

AI orchestration and RAG (Retrieval-Augmented Generation) platform for SADC organizations.

Built for hybrid dense+sparse search, multi-tenant isolation, and SADC network resilience.

## Quick Start (Demo)

```bash
# Prerequisites: Python 3.12, Podman or Docker
python scripts/verify-platform.py
make setup
cp .env.example .env  # Fill in ANTHROPIC_API_KEY
make dev-up
curl http://localhost:8000/health
```

## Run a POC Demo

```bash
./scripts/instant-poc.sh --prospect "Ministry of Health" --docs ./sample-docs/
```

## Deploy to Client Server

```bash
CLIENT_HOST=192.168.1.100 CLIENT_USER=ubuntu TENANT_ID=client-abc ./scripts/deploy-client.sh
```

## Phase 0 — Consulting MVP

This is the consulting MVP. Full SaaS platform (billing, analytics, K8s) comes after first paid invoice.

See [marketing/freelancer-packages.md](marketing/freelancer-packages.md) for service offerings.
See [marketing/case-study-rstp.md](marketing/case-study-rstp.md) for proof of capability.

## Architecture

- **RAG Engine**: Hybrid dense (BGE-large) + sparse (Splade) -> RRF fusion -> MiniLM reranking
- **Multi-tenant**: JWT-verified per-tenant Qdrant collections
- **Resilience**: CircuitBreaker (CLOSED/OPEN/HALF_OPEN) + SQLite WAL offline buffer
- **Customization**: `Hookable.execute()` — client overrides without forking core

## Requirements

- Python 3.12+
- Podman 5.x or Docker
- 4GB+ RAM (for embedding model)
- Linux or macOS (Apple Silicon supported), WSL2 on Windows
