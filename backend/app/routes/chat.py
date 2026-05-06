"""Chat endpoint that brokers messages to the Foundry agent."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..agent import agent_service
from ..db import get_session

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None
    customer_email: str | None = None


class ChatResponse(BaseModel):
    thread_id: str
    reply: str


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, session: AsyncSession = Depends(get_session)) -> ChatResponse:
    thread_id = await agent_service.ensure_thread(req.thread_id)
    prefix = f"[customer_email={req.customer_email}] " if req.customer_email else ""
    reply = await agent_service.ask(session, thread_id, prefix + req.message)
    return ChatResponse(thread_id=thread_id, reply=reply)
