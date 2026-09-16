"""Real-time Event Broadcasting Pipeline for Live Fraud Monitoring.

Supports both WebSocket subscribers and Server-Sent Events (SSE) streams
for instant alert dissemination to investigator dashboards.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from fastapi import WebSocket

logger = logging.getLogger("fraudlens.events")


class EventBroadcaster:
    """Thread-safe singleton event broker managing active client connections."""

    _instance: Optional["EventBroadcaster"] = None

    def __init__(self) -> None:
        self._active_websockets: Set[WebSocket] = set()
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._recent_events: List[Dict[str, Any]] = []
        self._max_recent: int = 50
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "EventBroadcaster":
        """Get or initialize singleton broadcaster instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect_websocket(self, websocket: WebSocket) -> None:
        """Register new active WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._active_websockets.add(websocket)
        logger.info("WebSocket client connected. Total active: %d", len(self._active_websockets))

        # Send recent events buffer to initialize client HUD
        for ev in self._recent_events[-10:]:
            try:
                await websocket.send_text(json.dumps(ev))
            except Exception:
                break

    async def disconnect_websocket(self, websocket: WebSocket) -> None:
        """Unregister closed WebSocket connection."""
        async with self._lock:
            self._active_websockets.discard(websocket)
        logger.info("WebSocket client disconnected. Total active: %d", len(self._active_websockets))

    async def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast an event to all connected WebSocket subscribers and the SSE queue."""
        event_payload = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        # Maintain recent buffer
        async with self._lock:
            self._recent_events.append(event_payload)
            if len(self._recent_events) > self._max_recent:
                self._recent_events.pop(0)

        # Broadcast across active WebSockets
        disconnected: Set[WebSocket] = set()
        message_text = json.dumps(event_payload)

        async with self._lock:
            active_sockets = list(self._active_websockets)

        for ws in active_sockets:
            try:
                await ws.send_text(message_text)
            except Exception:
                disconnected.add(ws)

        if disconnected:
            async with self._lock:
                for dead_ws in disconnected:
                    self._active_websockets.discard(dead_ws)

        # Enqueue for SSE consumers
        try:
            self._event_queue.put_nowait(event_payload)
        except asyncio.QueueFull:
            try:
                self._event_queue.get_nowait()
                self._event_queue.put_nowait(event_payload)
            except Exception:
                pass

    def sync_broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        """Synchronous wrapper to emit events from standard synchronous request threads."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast(event_type, data))
            else:
                loop.run_until_complete(self.broadcast(event_type, data))
        except RuntimeError:
            # Handle thread context without running event loop
            try:
                new_loop = asyncio.new_event_loop()
                new_loop.run_until_complete(self.broadcast(event_type, data))
                new_loop.close()
            except Exception as e:
                logger.debug("Failed to dispatch broadcast in background thread: %s", e)

    async def sse_event_generator(self) -> AsyncGenerator[str, None]:
        """Async generator yielding Server-Sent Events formatted strings."""
        while True:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=15.0)
                yield f"event: {event['event_type']}\ndata: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                # Keep-alive heartbeat ping
                yield ": ping\n\n"

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent events buffer."""
        return self._recent_events[-limit:]
