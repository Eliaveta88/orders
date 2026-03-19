"""Session tracking for debugging and logging."""

from typing import Any


class SessionTracker:
    """Tracks active database sessions for debugging."""

    _sessions: dict[str, Any] = {}

    @classmethod
    def track_session(cls, session: Any, context: str = "") -> str:
        """Register a session and return its tracking id."""
        sid = f"{id(session)}_{context}"
        cls._sessions[sid] = session
        return sid

    @classmethod
    def untrack_session(cls, session_id: str) -> None:
        """Remove a session from tracking."""
        cls._sessions.pop(session_id, None)
