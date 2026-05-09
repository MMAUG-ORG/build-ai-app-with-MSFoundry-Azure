"""Create (or update) the Microsoft Foundry agent for the support app.

Run automatically by `azd up` (postprovision hook in azure.yaml).
Reads endpoint + model from azd outputs and writes the resulting agent id
back to the API App Service as FOUNDRY_AGENT_ID.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from azure.ai.agents.models import FunctionTool, ToolDefinition
from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential, DefaultAzureCredential

AGENT_NAME = "mmaug-support-agent"
AGENT_INSTRUCTIONS = """
You are the customer support agent for Contoso Malta. Be concise, friendly, and professional.

Always:
1. Identify the customer by their email (the user message is prefixed with [customer_email=...]).
2. If the issue is new, call `create_ticket` with a short subject and a sensible priority
   (low / normal / high / urgent). Confirm the ticket number to the customer.
3. If the customer references an existing ticket id, call `lookup_ticket` first.
4. If they ask "what tickets do I have", call `list_open_tickets`.
5. End every reply with a clear next step.
""".strip()

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Open a new support ticket for a customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_email": {"type": "string"},
                    "subject": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent"],
                    },
                },
                "required": ["customer_email", "subject"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_ticket",
            "description": "Retrieve details for a single ticket by id.",
            "parameters": {
                "type": "object",
                "properties": {"ticket_id": {"type": "integer"}},
                "required": ["ticket_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_open_tickets",
            "description": "List all open tickets for a given customer email.",
            "parameters": {
                "type": "object",
                "properties": {"customer_email": {"type": "string"}},
                "required": ["customer_email"],
            },
        },
    },
]


def _azd_env() -> dict[str, str]:
    """Return azd environment values as a dict."""
    try:
        out = subprocess.check_output(["azd", "env", "get-values", "--output", "json"])
        return json.loads(out)
    except Exception as exc:
        print(f"warn: could not read azd env ({exc}); falling back to os.environ", file=sys.stderr)
        return dict(os.environ)


def _credential():
    # Prefer the CLI credential during local/azd runs so user gets the access token.
    try:
        return AzureCliCredential()
    except Exception:
        return DefaultAzureCredential()


def main() -> int:
    env = _azd_env()
    endpoint = env.get("FOUNDRY_PROJECT_ENDPOINT")
    model = env.get("FOUNDRY_MODEL_DEPLOYMENT", "gpt-4o-mini")
    if not endpoint:
        print("error: FOUNDRY_PROJECT_ENDPOINT not set", file=sys.stderr)
        return 1

    project = AIProjectClient(endpoint=endpoint, credential=_credential())
    agents = project.agents

    # Reuse existing agent by name if present.
    existing_id: str | None = None
    for agent in agents.list_agents():
        if agent.name == AGENT_NAME:
            existing_id = agent.id
            break

    if existing_id:
        agent = agents.update_agent(
            agent_id=existing_id,
            model=model,
            instructions=AGENT_INSTRUCTIONS,
            tools=TOOLS,
        )
        print(f"updated agent: {agent.id}")
    else:
        agent = agents.create_agent(
            model=model,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            tools=TOOLS,
        )
        print(f"created agent: {agent.id}")

    # Persist for App Service + future runs.
    subprocess.check_call(["azd", "env", "set", "FOUNDRY_AGENT_ID", agent.id])

    api_app = env.get("API_HOSTNAME", "").split(".")[0]
    rg = env.get("AZURE_RESOURCE_GROUP")
    sub = env.get("AZURE_SUBSCRIPTION_ID")
    if api_app and rg:
        cmd = [
            "az", "webapp", "config", "appsettings", "set",
            "-g", rg, "-n", api_app,
            "--settings", f"FOUNDRY_AGENT_ID={agent.id}",
        ]
        if sub:
            cmd.extend(["--subscription", sub])
        subprocess.check_call(cmd)
        print(f"set FOUNDRY_AGENT_ID on {api_app}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
