"""
MindCare AI — Core Agent (High Performance & Multi-Model Failover)
Supports real-time SSE token streaming, instant model failover,
and zero-latency local mood/emotion analysis to preserve API quotas.
"""
import asyncio
import json
import logging
import re
from typing import AsyncGenerator

from langchain_openai import ChatOpenAI
try:
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
except ImportError:
    from langchain.schema import SystemMessage, HumanMessage, AIMessage

from config import settings
from agent.lc_memory import get_history_messages, save_exchange
from agent.prompts import SYSTEM_PROMPT, MOOD_ANALYSIS_PROMPT
from agent.safety import safety_checker
from agent.psych_kb import retrieve_clinical_context

logger = logging.getLogger(__name__)

# ─── LLM Instance Cache ──────────────────────────────────────────────────────
# Caches ChatOpenAI instances per (model, streaming) to avoid recreation overhead
_llm_cache: dict[tuple[str, bool], ChatOpenAI] = {}


def get_llm(model_name: str, streaming: bool = False) -> ChatOpenAI:
    """Return or create a ChatOpenAI client with fast timeout and zero internal retries."""
    cache_key = (model_name, streaming)
    if cache_key not in _llm_cache:
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        _llm_cache[cache_key] = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            openai_api_key=api_key,
            base_url=settings.GEMINI_BASE_URL,
            openai_api_base=settings.GEMINI_BASE_URL,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
            streaming=streaming,
            request_timeout=settings.REQUEST_TIMEOUT,
            max_retries=0,  # Fast failover handled by our multi-model loop
        )
    return _llm_cache[cache_key]


def _build_messages(user_message: str, session_id: str, is_crisis: bool):
    """Build the LangChain message list (system + clinical articles + sliding-window history + user)."""
    sys_content = SYSTEM_PROMPT
    if is_crisis:
        sys_content += (
            "\n\n⚠️ CRISIS DETECTED: The user may be in danger. "
            "Respond with maximum compassion, validate their feelings, "
            "and gently but clearly provide crisis resources. "
            f"Include this hotline: {settings.CRISIS_HOTLINE}"
        )

    # Dynamically inject relevant clinical psychology concepts and articles
    try:
        clinical_evidence = retrieve_clinical_context(user_message)
        if clinical_evidence:
            sys_content += f"\n\n{clinical_evidence}"
    except Exception as exc:
        logger.warning("Clinical context retrieval skipped: %s", exc)

    # Use trimmed history keyed by session_id
    history = get_history_messages(session_id)
    return [SystemMessage(content=sys_content)] + history + [HumanMessage(content=user_message)]


# ─── Streaming chat (SSE with automatic model failover) ───────────────────────
async def chat_stream(
    session_id: str,
    user_message: str,
    username: str = "guest",
) -> AsyncGenerator[str, None]:
    """
    Yield reply tokens one-by-one for Server-Sent Events.
    If the primary model hits 429 quota exhaustion or 503, immediately
    fails over to the next candidate model in settings.FALLBACK_MODELS.
    """
    safety = safety_checker.check(user_message)
    # Key memory by session_id to isolate conversations and keep payload lean
    memory_key = session_id or username
    messages = _build_messages(user_message, memory_key, safety["is_crisis"])

    # Yield crisis metadata first if detected
    if safety["is_crisis"]:
        crisis_event = json.dumps({
            "type": "crisis",
            "crisis_message": safety["crisis_message"],
            "hotline": safety["hotline"],
        })
        yield f"event: crisis\ndata: {crisis_event}\n\n"

    full_reply_parts: list[str] = []
    stream_succeeded = False

    # Multi-model failover loop
    for model_name in settings.FALLBACK_MODELS:
        llm = get_llm(model_name, streaming=True)
        try:
            logger.info("chat_stream: Streaming with model '%s'...", model_name)
            async for chunk in llm.astream(messages):
                token = chunk.content
                if token:
                    full_reply_parts.append(token)
                    yield f"data: {json.dumps({'token': token})}\n\n"

            if full_reply_parts:
                stream_succeeded = True
                break
        except Exception as exc:
            logger.warning(
                "chat_stream: Model '%s' encountered error: %s. Trying next fallback...",
                model_name, exc
            )
            # If some tokens were already yielded before failure, continue or reset
            if full_reply_parts:
                stream_succeeded = True
                break
            continue

    if not stream_succeeded or not full_reply_parts:
        error_msg = (
            "I'm here with you, but I'm experiencing a momentary connection slowdown. "
            "Please try sending your message again."
        )
        yield f"data: {json.dumps({'token': error_msg})}\n\n"
        full_reply_parts.append(error_msg)

    full_reply = "".join(full_reply_parts)

    # Persist exchange to memory
    save_exchange(memory_key, user_message, full_reply)

    # Send final done event with metadata
    done_event = json.dumps({
        "type": "done",
        "session_id": session_id,
        "is_crisis": safety["is_crisis"],
        "crisis_message": safety["crisis_message"],
        "hotline": safety["hotline"],
        "full_reply": full_reply,
    })
    yield f"event: done\ndata: {done_event}\n\n"


# ─── Non-streaming chat (fallback with model failover) ────────────────────────
async def chat(session_id: str, user_message: str, username: str = "guest") -> dict:
    """
    Generate a therapeutic AI reply (non-streaming).
    Tries fallback models automatically if the primary model fails or hits quota limits.
    """
    safety = safety_checker.check(user_message)
    memory_key = session_id or username
    messages = _build_messages(user_message, memory_key, safety["is_crisis"])

    last_error = None
    for model_name in settings.FALLBACK_MODELS:
        llm = get_llm(model_name, streaming=False)
        try:
            logger.info("chat: invoking model '%s'...", model_name)
            response = await llm.ainvoke(messages)
            reply = response.content.strip()
            if reply:
                save_exchange(memory_key, user_message, reply)
                return {
                    "reply": reply,
                    "is_crisis": safety["is_crisis"],
                    "crisis_message": safety["crisis_message"],
                    "hotline": safety["hotline"],
                    "session_id": session_id,
                }
        except Exception as exc:
            logger.warning("chat: model '%s' error: %s. Trying next...", model_name, exc)
            last_error = exc
            continue

    raise RuntimeError(f"All AI models exhausted. Last error: {last_error}")


# ─── High-speed zero-latency mood & emotion analyzer ────────────────────────
# Instant rule-based emotional analyzer that preserves API quota and executes in <1ms
_EMOTION_KEYWORDS = {
    "anxious": ["anxious", "anxiety", "panic", "worried", "nervous", "fear", "scared", "overwhelmed", "dread"],
    "sad": ["sad", "depressed", "unhappy", "crying", "miserable", "heartbroken", "down", "gloomy", "hopeless"],
    "stressed": ["stress", "stressed", "pressure", "exhausted", "burnout", "tired", "too much", "deadline"],
    "lonely": ["lonely", "alone", "isolated", "nobody", "no one", "empty", "abandoned"],
    "angry": ["angry", "mad", "furious", "frustrated", "irritated", "annoyed", "hate"],
    "calm": ["calm", "peaceful", "better", "relaxed", "fine", "okay", "alright", "good"],
    "hopeful": ["hopeful", "grateful", "thankful", "happy", "relieved", "excited", "optimistic"],
}

_THEME_KEYWORDS = {
    "academics_work": ["exam", "test", "study", "studies", "school", "college", "job", "work", "career", "boss", "interview"],
    "relationships": ["family", "mom", "dad", "parent", "friend", "friends", "partner", "boyfriend", "girlfriend", "breakup"],
    "health_sleep": ["sleep", "insomnia", "headache", "sick", "appetite", "pain", "energy"],
    "self_worth": ["failure", "not good enough", "worthless", "insecure", "guilt", "shame", "confidence"],
}


async def analyze_mood(message: str) -> dict:
    """
    Fast emotional analysis executed locally in <1ms.
    Eliminates secondary API calls that double API quota usage and cause 429 rate limit errors.
    """
    text = message.lower()
    scores: dict[str, int] = {}

    for emotion, words in _EMOTION_KEYWORDS.items():
        count = sum(1 for w in words if re.search(r"\b" + re.escape(w) + r"\b", text))
        if count:
            scores[emotion] = count

    # Detect primary emotion
    if scores:
        primary_emotion = max(scores, key=scores.get)
    else:
        primary_emotion = "reflective"

    # Compute intensity (1-10)
    base_intensity = 5
    if primary_emotion in {"anxious", "sad", "stressed", "angry"}:
        base_intensity = 7
    elif primary_emotion in {"calm", "hopeful"}:
        base_intensity = 3

    # Adjust for intensifiers
    if any(w in text for w in ["extremely", "very", "can't take", "so much", "unbearable", "desperately", "really"]):
        base_intensity = min(10, base_intensity + 2)
    if "!" in message:
        base_intensity = min(10, base_intensity + 1)

    # Detect themes
    key_themes = []
    for theme, words in _THEME_KEYWORDS.items():
        if any(w in text for w in words):
            key_themes.append(theme.replace("_", " "))

    safety = safety_checker.check(message)

    return {
        "primary_emotion": primary_emotion,
        "intensity": base_intensity,
        "crisis_risk": safety["is_crisis"],
        "key_themes": key_themes or ["general well-being"],
    }


# ─── Session ID generator ────────────────────────────────────────────────────
def new_session_id() -> str:
    """Generate a unique session ID."""
    import uuid
    return str(uuid.uuid4())
