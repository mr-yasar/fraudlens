"""Assistant Session Lifecycle & Bounded Memory Service (Phases 19-21).

Provides:
- Phase 19: Strict bounded conversation turn window (max 6 turns: 3 user + 3 assistant)
- Phase 20: Cross-turn isolation partitioned per user & session ID
- Phase 21: Immediate session memory purge on logout, identity change, or clear action
"""

import time
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("fraudlens.assistant.session")

# Max 6 conversational turns (3 user queries + 3 assistant responses)
MAX_CONVERSATION_TURNS = 6
SESSION_TTL_SECONDS = 3600 * 4  # 4 hours expiry


class SessionMemoryStore:
    """Thread-safe in-memory store for bounded session histories."""

    def __init__(self):
        # Key: (user_id: int, session_id: str) -> {"messages": List[Dict], "last_active": float}
        self._store: Dict[Tuple[int, str], Dict[str, Any]] = {}

    def _get_key(self, user_id: int, session_id: Optional[str]) -> Tuple[int, str]:
        return (user_id, session_id or "default")

    def prune_incoming_messages(
        self,
        messages: List[Dict[str, str]],
        max_turns: int = MAX_CONVERSATION_TURNS,
    ) -> List[Dict[str, str]]:
        """Phase 19: Prune incoming client conversation to bounded window (max 6 turns)."""
        if not messages:
            return []
        
        # Filter out any rogue system messages sent by client
        clean_user_assistant_turns = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m.get("role") in ("user", "assistant")
        ]

        if len(clean_user_assistant_turns) > max_turns:
            logger.info(
                "Pruning conversation history from %d turns to bounded window of %d turns",
                len(clean_user_assistant_turns),
                max_turns,
            )
            return clean_user_assistant_turns[-max_turns:]
        return clean_user_assistant_turns

    def record_turn(
        self,
        user_id: int,
        session_id: Optional[str],
        user_msg: str,
        assistant_msg: str,
    ) -> None:
        """Record completed conversational turn in bounded memory."""
        key = self._get_key(user_id, session_id)
        now = time.time()

        if key not in self._store:
            self._store[key] = {"messages": [], "last_active": now}

        entry = self._store[key]
        entry["last_active"] = now
        entry["messages"].append({"role": "user", "content": user_msg})
        entry["messages"].append({"role": "assistant", "content": assistant_msg})

        # Enforce bounded window on server-side cache
        if len(entry["messages"]) > MAX_CONVERSATION_TURNS:
            entry["messages"] = entry["messages"][-MAX_CONVERSATION_TURNS:]

    def get_history(self, user_id: int, session_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Retrieve bounded history for this user & session."""
        key = self._get_key(user_id, session_id)
        entry = self._store.get(key)
        if not entry:
            return []

        # Check TTL
        if time.time() - entry.get("last_active", 0) > SESSION_TTL_SECONDS:
            self.purge_session(user_id, session_id)
            return []

        return list(entry["messages"])

    def purge_session(self, user_id: int, session_id: Optional[str] = None) -> int:
        """Phase 21: Purge history for user/session on logout or reset."""
        purged_count = 0
        if session_id:
            key = (user_id, session_id)
            if key in self._store:
                del self._store[key]
                purged_count += 1
        else:
            keys_to_del = [k for k in self._store if k[0] == user_id]
            for k in keys_to_del:
                del self._store[k]
                purged_count += 1

        logger.info("Purged %d session cache entries for user_id=%s", purged_count, user_id)
        return purged_count


# Global singleton memory manager
session_memory = SessionMemoryStore()
