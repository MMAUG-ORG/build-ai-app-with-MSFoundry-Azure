"""Ticket read endpoints (CRUD-lite)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import Customer, Ticket, get_session

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("")
async def list_tickets(session: AsyncSession = Depends(get_session)) -> list[dict]:
    stmt = select(Ticket).order_by(Ticket.created_at.desc()).limit(100)
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "priority": t.priority,
            "customer_id": t.customer_id,
            "created_at": t.created_at.isoformat(),
        }
        for t in rows
    ]


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(404, "Ticket not found")
    customer = await session.get(Customer, ticket.customer_id)
    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "status": ticket.status,
        "priority": ticket.priority,
        "summary": ticket.summary,
        "customer_email": customer.email if customer else None,
        "created_at": ticket.created_at.isoformat(),
    }
