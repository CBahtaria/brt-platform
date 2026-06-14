# Case Study: Eswatini Government AI Document Intelligence

## Client
Eswatini Government — RSTP (Regional Spatial Technology Platform)

## Challenge
Government staff needed to search across thousands of policy documents, regulations,
and reports. Manual search was slow and inconsistent across departments.

## Solution
BRT Platform (then: RSTP Swarm) — a hybrid RAG system combining:
- Dense semantic search (BAAI/bge-large-en-v1.5)
- Sparse keyword search (BM25/Splade)
- Cross-encoder re-ranking (MiniLM-L-6-v2)
- Deployed on government servers via Podman Compose
- WhatsApp-based incident alerting for operations team

## Architecture
- **Qdrant** vector database (single-node, 4GB RAM)
- **FastAPI** REST API with streaming responses
- **Anthropic Claude** for answer generation
- **Prometheus + Grafana** for query metrics
- Fully air-gapped deployment option

## Results
- Sub-2-second query response times (p95)
- Cross-department document discovery improved
- Zero downtime over 3-month deployment period
- Operational by solo developer from initial brief

## Technology Stack
Python 3.12 · FastAPI · Qdrant · Sentence-Transformers · Podman · Prometheus

---

*Available as a reference. Contact info@brtinc.dev to discuss your use case.*
