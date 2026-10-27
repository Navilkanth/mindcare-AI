"""
MindCare AI — Chat Route (Streaming + Non-Streaming fallback)
POST /api/chat/stream — Fast SSE real-time token stream
POST /api/chat        — Non-streaming fallback
"""
import json
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from data.models import ChatRequest, ChatResponse
from data import database
from agent import core

logger = logging.getLogger(__name__)
router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────────
#  SSE STREAMING endpoint — delivers tokens in real-time
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Stream AI response tokens via Server-Sent Events.
    The frontend receives tokens as they are generated — zero wait time.
    """
    session_id = request.session_id or core.new_session_id()

    # Fire-and-forget DB session & user message creation
    background_tasks.add_task(database.create_session, session_id)
    background_tasks.add_task(database.save_message, session_id, "user", request.message)
    background_tasks.add_task(database.update_session_activity, session_id)

    # Instant zero-quota mood analysis in background
    async def _log_mood():
        try:
            mood = await core.analyze_mood(request.message)
            database.save_mood_log(
                session_id=session_id,
                mood_score=mood.get("intensity", 5),
                primary_emotion=mood.get("primary_emotion"),
                ai_intensity=mood.get("intensity"),
                key_themes=mood.get("key_themes", []),
            )
        except Exception as e:
            logger.debug("Mood logging skipped: %s", e)

    background_tasks.add_task(_log_mood)

    async def event_generator():
        collected_reply = []
        try:
            async for chunk in core.chat_stream(session_id, request.message):
                yield chunk
                if chunk.startswith("data: "):
                    try:
                        payload = json.loads(chunk[6:].strip())
                        if "token" in payload:
                            collected_reply.append(payload["token"])
                        elif payload.get("type") == "done" and payload.get("full_reply"):
                            collected_reply = [payload["full_reply"]]
                    except Exception:
                        pass
        finally:
            # When the stream finishes, save the complete AI response to DB
            ai_text = "".join(collected_reply).strip()
            if ai_text:
                try:
                    database.save_message(session_id, "assistant", ai_text)
                except Exception as exc:
                    logger.error("Failed to save stream reply to database: %s", exc)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",   # Disable reverse-proxy buffering
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
#  NON-STREAMING fallback
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
):
    """
    Send a user message and get a therapeutic AI response (non-streaming).
    """
    session_id = request.session_id or core.new_session_id()

    background_tasks.add_task(database.create_session, session_id)
    background_tasks.add_task(database.save_message, session_id, "user", request.message)
    background_tasks.add_task(database.update_session_activity, session_id)

    try:
        result = await core.chat(session_id, request.message)
    except Exception as e:
        logger.error(f"AI error: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {str(e)}"
        )

    # Save AI response in background
    background_tasks.add_task(database.save_message, session_id, "assistant", result["reply"])

    # Instant mood analysis in background
    async def _log_mood():
        try:
            mood = await core.analyze_mood(request.message)
            database.save_mood_log(
                session_id=session_id,
                mood_score=mood.get("intensity", 5),
                primary_emotion=mood.get("primary_emotion"),
                ai_intensity=mood.get("intensity"),
                key_themes=mood.get("key_themes", []),
            )
        except Exception:
            pass

    background_tasks.add_task(_log_mood)

    return ChatResponse(**result)
