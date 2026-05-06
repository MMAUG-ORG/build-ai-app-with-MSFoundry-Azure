"""Microsoft Foundry Agent client + local function-tool implementations.

Tools the agent can call:
    create_ticket(customer_email, subject, priority)
    lookup_ticket(ticket_id)
    list_open_tickets(customer_email)
"""
from __future__ import annotations

import json
from typing import Any

from azure.ai.agents.models import (
    RequiredFunctionToolCall,
    SubmitToolOutputsAction,
    ToolOutput,
)
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import Customer, Ticket

# The Foundry / Azure clients are constructed lazily so that importing this
# module (e.g. in CI smoke tests, unit tests, or `python -c "from app.main
# import app"`) never requires real Foundry credentials or environment vars.
_credential: DefaultAzureCredential | None = None
_project: AIProjectClient | None = None


def _get_credential() -> DefaultAzureCredential:
    global _credential
    if _credential is None:
        _credential = DefaultAzureCredential()
    return _credential


def _get_project() -> AIProjectClient:
    global _project
    if _project is None:
        _project = AIProjectClient(
            endpoint=get_settings().foundry_project_endpoint,
            credential=_get_credential(),
        )
    return _project


# ---------- Tool implementations (executed locally) ----------

async def _create_ticket(
    session: AsyncSession, customer_email: str, subject: str, priority: str = "normal"
) -> dict[str, Any]:
    result = await session.execute(select(Customer).where(Customer.email == customer_email))
    customer = result.scalar_one_or_none()
    if customer is None:
        customer = Customer(email=customer_email, name=customer_email.split("@")[0])
        session.add(customer)
        await session.flush()
    ticket = Ticket(customer_id=customer.id, subject=subject, priority=priority)
    session.add(ticket)
    await session.flush()
    await session.commit()
    return {"ticket_id": ticket.id, "status": ticket.status, "priority": ticket.priority}


async def _lookup_ticket(session: AsyncSession, ticket_id: int) -> dict[str, Any]:
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        return {"error": f"Ticket {ticket_id} not found"}
    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "status": ticket.status,
        "priority": ticket.priority,
        "summary": ticket.summary,
    }


async def _list_open_tickets(session: AsyncSession, customer_email: str) -> dict[str, Any]:
    stmt = (
        select(Ticket)
        .join(Customer)
        .where(Customer.email == customer_email, Ticket.status == "open")
    )
    result = await session.execute(stmt)
    tickets = result.scalars().all()
    return {"tickets": [{"id": t.id, "subject": t.subject} for t in tickets]}


TOOL_DEFS: list[dict[str, Any]] = [
    {
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
    {
        "name": "lookup_ticket",
        "description": "Retrieve details for a single ticket by id.",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer"}},
            "required": ["ticket_id"],
        },
    },
    {
        "name": "list_open_tickets",
        "description": "List all open tickets for a given customer email.",
        "parameters": {
            "type": "object",
            "properties": {"customer_email": {"type": "string"}},
            "required": ["customer_email"],
        },
    },
]


async def _dispatch_tool(session: AsyncSession, name: str, args: dict[str, Any]) -> Any:
    if name == "create_ticket":
        return await _create_ticket(session, **args)
    if name == "lookup_ticket":
        return await _lookup_ticket(session, **args)
    if name == "list_open_tickets":
        return await _list_open_tickets(session, **args)
    return {"error": f"Unknown tool {name}"}


# ---------- Public API ----------

class AgentService:
    def __init__(self) -> None:
        self._agent_id: str | None = None

    @property
    def agent_id(self) -> str:
        if self._agent_id is None:
            self._agent_id = get_settings().foundry_agent_id
        return self._agent_id

    async def ensure_thread(self, thread_id: str | None) -> str:
        if thread_id:
            return thread_id
        thread = await _get_project().agents.threads.create()
        return thread.id

    async def ask(self, session: AsyncSession, thread_id: str, user_message: str) -> str:
        agents = _get_project().agents
        await agents.messages.create(thread_id=thread_id, role="user", content=user_message)
        run = await agents.runs.create(thread_id=thread_id, agent_id=self.agent_id)

        # Poll the run, executing local tool calls when requested.
        while run.status in ("queued", "in_progress", "requires_action"):
            if run.status == "requires_action" and isinstance(
                run.required_action, SubmitToolOutputsAction
            ):
                outputs: list[ToolOutput] = []
                for call in run.required_action.submit_tool_outputs.tool_calls:
                    if not isinstance(call, RequiredFunctionToolCall):
                        continue
                    args = json.loads(call.function.arguments or "{}")
                    result = await _dispatch_tool(session, call.function.name, args)
                    outputs.append(
                        ToolOutput(tool_call_id=call.id, output=json.dumps(result))
                    )
                run = await agents.runs.submit_tool_outputs(
                    thread_id=thread_id, run_id=run.id, tool_outputs=outputs
                )
            else:
                run = await agents.runs.get(thread_id=thread_id, run_id=run.id)

        if run.status != "completed":
            return f"(agent run ended with status: {run.status})"

        messages = agents.messages.list(thread_id=thread_id, order="desc", limit=1)
        async for msg in messages:
            if msg.role == "assistant":
                for part in msg.content:
                    text = getattr(part, "text", None)
                    if text and getattr(text, "value", None):
                        return text.value
        return ""


agent_service = AgentService()
