"""
MindCare AI — Mood Tracking Route
GET  /api/mood/{session_id}  — Get mood history
POST /api/mood               — Log a manual mood entry
"""
from fastapi import APIRouter, HTTPException
from data.models import MoodLogRequest, MoodLogResponse
from data import database

router = APIRouter()


@router.post("/mood", response_model=MoodLogResponse)
async def log_mood(request: MoodLogRequest):
    """Manually log a mood score (1-10) for a session."""
    database.save_mood_log(
        session_id=request.session_id,
        mood_score=request.mood_score,
        note=request.note,
    )
    return MoodLogResponse(success=True, message="Mood logged successfully.")


@router.get("/mood/{session_id}")
async def get_mood_history(session_id: str):
    """Get all mood logs for a session."""
    logs = database.get_mood_logs(session_id)
    return {"session_id": session_id, "mood_logs": logs}
