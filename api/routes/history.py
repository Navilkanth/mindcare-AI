"""
MindCare AI — Conversation History Route
GET /api/history/{session_id} — Get full chat history for a session
"""
from fastapi import APIRouter
from data import database

router = APIRouter()


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Retrieve all messages for a given session."""
    messages = database.get_messages(session_id)
    return {"session_id": session_id, "messages": messages}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear in-memory conversation history for a session (DB records stay)."""
    from agent.memory import memory
    from agent.lc_memory import clear_memory as clear_lc_memory
    memory.clear_session(session_id)
    clear_lc_memory(session_id)
    return {"success": True, "message": f"Session {session_id} cleared from memory."}
