# Live demo script — 9 May 2026

> ~10 minutes. Have the deployed Web URL open in one tab and the Foundry
> portal in another so you can show the agent thread + tool-call traces.

## 1 · Show the architecture (1 min)
- Open `README.md` and walk through the 3-tier diagram.
- Highlight: **no API keys** — everything is Managed Identity + Entra.

## 2 · Tour the code (3 min)
- `backend/app/agent.py` — the Foundry agent loop, especially `requires_action`
  and the local tool dispatcher.
- `scripts/create_agent.py` — declarative agent creation; rerunning updates in place.
- `infra/main.bicep` — single file wires Foundry, Postgres, Storage, App Service x2,
  and assigns `Storage Blob Data Contributor` + `Azure AI User` to the API identity.

## 3 · Run the demo (5 min)
1. In the web app, send: **"Hi, I'm locked out of the dashboard since this morning."**
   - Expect: agent calls `create_ticket(priority=high)` → ticket appears in the right pane.
2. Send: **"What tickets do I have open?"**
   - Expect: agent calls `list_open_tickets` and replies with a numbered list.
3. Send: **"Update on ticket #1?"** then **"Thanks!"**
   - Expect: `lookup_ticket` call followed by a polite closing.
4. Switch to Foundry portal → Threads → show the same conversation with tool traces.

## 4 · Wrap (1 min)
- Show `azd down --purge` (don't run it live — point at the command).
- Share the repo link and the [MMAUG community articles](https://github.com/MMAUG-ORG/community-articles).
