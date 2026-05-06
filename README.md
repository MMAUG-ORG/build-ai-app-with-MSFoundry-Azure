# Build an AI App with Microsoft Foundry & Azure

A fully automated **AI Agent–powered Customer Support App** for the
Malta Microsoft AI User Group session (Saturday, 9 May 2026).

Inspired by the
[Azure-Language-OpenAI-Conversational-Agent-Accelerator](https://github.com/Azure-Samples/Azure-Language-OpenAI-Conversational-Agent-Accelerator),
trimmed to a clean 3-tier reference you can deploy in one command.

## Architecture (3-tier)

```
┌─────────────────────────┐    ┌─────────────────────────┐    ┌────────────────────────────┐
│   Frontend (React/Vite) │ ─▶ │   Backend (FastAPI)     │ ─▶ │  Microsoft Foundry Agent   │
│   Azure App Service     │    │   Azure App Service     │    │  (gpt-4o-mini)             │
└─────────────────────────┘    └────────────┬────────────┘    └────────────────────────────┘
                                            │
                            ┌───────────────┼────────────────┐
                            ▼                                ▼
                ┌────────────────────┐           ┌────────────────────────────┐
                │ Azure DB for       │           │ Azure Storage (Blob)       │
                │ PostgreSQL Flex.   │           │ Ticket attachments         │
                └────────────────────┘           └────────────────────────────┘
```

| Tier               | Tech                                         | Azure Resource                  |
|--------------------|----------------------------------------------|---------------------------------|
| User Experience    | React 18 + Vite + TypeScript                 | App Service (Linux, Node 20)    |
| Backend / API      | Python 3.11 + FastAPI + SQLAlchemy (async)   | App Service (Linux, Python 3.11)|
| AI Agent           | Microsoft Foundry Agent (azure-ai-agents)    | Azure AI Foundry project        |
| Relational data    | Customers, tickets, messages                 | Azure DB for PostgreSQL Flex.   |
| Unstructured data  | Attachments, transcripts                     | Azure Blob Storage              |
| Identity           | Managed Identity end-to-end (no secrets)     | Entra ID                        |

## Repo layout

```
build-ai-app-with-foundry-codes/
├── backend/        FastAPI service – exposes /chat, /tickets, /uploads
├── frontend/       React chat UI
├── infra/          Bicep + azd template (one-shot deploy)
├── scripts/        Foundry agent bootstrap + Postgres seed
└── azure.yaml      Azure Developer CLI manifest
```

## Quick start (local)

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill values
uvicorn app.main:app --reload --port 8000

# 2. Frontend
cd ../frontend
npm install
cp .env.example .env.local    # VITE_API_BASE=http://localhost:8000
npm run dev
```

## Deploy to Azure (one command)

```bash
cd build-ai-app-with-foundry-codes
azd auth login
azd up                        # provisions infra + deploys both apps
```

`azd up` will:

1. Provision: Foundry project, gpt-4o-mini deployment, Postgres Flex, Storage, 2× App Service.
2. Wire managed identity + RBAC (Cognitive Services User, Storage Blob Data Contributor, Postgres user).
3. Run `scripts/create_agent.py` post-deploy to create the support agent.
4. Build & deploy the React SPA and FastAPI service.

## Demo flow (for the session)

1. Show empty ticket list.
2. Customer sends a chat → backend forwards to Foundry Agent thread.
3. Agent calls the `create_ticket` tool → row appears in Postgres.
4. Customer uploads a screenshot → stored in Blob, linked to the ticket.
5. Agent calls `lookup_ticket` to summarise the case in plain English.

See [`scripts/demo-script.md`](scripts/demo-script.md) for the live walkthrough.
