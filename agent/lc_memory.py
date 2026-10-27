"""
MindCare AI — LangChain Conversation Memory (modern API)
Uses langchain_core.chat_history.InMemoryChatMessageHistory (no deprecated classes).
One history store per authenticated username.
"""
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from config import settings

# username → list of BaseMessage
_stores: dict[str, list[BaseMessage]] = {}


def get_history(username: str) -> list[BaseMessage]:
    """Return full message history for a user (creates empty list if new)."""
    if username not in _stores:
        _stores[username] = []
    return _stores[username]


def save_exchange(username: str, human_msg: str, ai_msg: str) -> None:
    """
    Append one Human+AI exchange to the user's history and apply
    a sliding window so the list never exceeds MAX_HISTORY_MESSAGES pairs.
    """
    history = get_history(username)
    history.append(HumanMessage(content=human_msg))
    history.append(AIMessage(content=ai_msg))

    # Keep only the most recent window to minimize prompt tokens and maximize speed
    max_msgs = settings.MAX_HISTORY_MESSAGES
    if len(history) > max_msgs:
        _stores[username] = history[-max_msgs:]


def get_history_messages(username: str) -> list[BaseMessage]:
    """
    Return the LangChain BaseMessage list ready to be inserted into
    a ChatPromptTemplate / direct LLM call between the SystemMessage
    and the new HumanMessage.
    """
    return list(get_history(username))


def clear_memory(username: str) -> None:
    """Wipe conversation history for a user."""
    _stores.pop(username, None)
