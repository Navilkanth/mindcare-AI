"""
MindCare AI — Conversation Memory Manager
Handles per-session message history with a sliding window.
"""
from collections import defaultdict
from typing import Optional
from config import settings


class ConversationMemory:
    """
    Stores conversation history per session_id in-memory.
    Applies a sliding window to avoid exceeding token limits.
    """

    def __init__(self):
        # session_id -> list of {"role": ..., "content": ...}
        self._sessions: dict[str, list[dict]] = defaultdict(list)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Append a message to the session's history."""
        self._sessions[session_id].append({"role": role, "content": content})
        # Enforce sliding window (keep system prompt + last N messages)
        self._trim(session_id)

    def get_history(self, session_id: str) -> list[dict]:
        """Return the full message history for a session."""
        return list(self._sessions[session_id])

    def get_messages_for_api(
        self, session_id: str, system_prompt: str
    ) -> list[dict]:
        """
        Return messages formatted for the OpenAI Chat API.
        Prepends the system prompt and includes only the most recent
        ``settings.MAX_HISTORY_MESSAGES`` entries to keep the payload small.
        """
        # Retrieve the full session history
        full_history = self._sessions.get(session_id, [])
        # Keep only the most recent messages (after the system prompt)
        recent = full_history[-settings.MAX_HISTORY_MESSAGES :]
        return [{"role": "system", "content": system_prompt}, *recent]


    def clear_session(self, session_id: str) -> None:
        """Wipe all history for a session."""
        self._sessions.pop(session_id, None)

    def get_session_ids(self) -> list[str]:
        """Return all active session IDs."""
        return list(self._sessions.keys())

    def session_exists(self, session_id: str) -> bool:
        return session_id in self._sessions

    def _trim(self, session_id: str) -> None:
        """Keep only the last MAX_HISTORY_MESSAGES messages."""
        max_msgs = settings.MAX_HISTORY_MESSAGES
        history = self._sessions[session_id]
        if len(history) > max_msgs:
            self._sessions[session_id] = history[-max_msgs:]


# Singleton instance shared across the app
memory = ConversationMemory()
