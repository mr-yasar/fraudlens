"""Real-Time Event Streaming Endpoints (WebSocket & SSE)."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse

from backend.app.core.security import decode_access_token
from backend.app.services.event_broadcaster import EventBroadcaster

router = APIRouter()
logger = logging.getLogger("fraudlens.events")


@router.websocket("/live-events")
async def websocket_live_events(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time fraud alert streaming.
    Clients receive instant notifications for PRE_AUTH_EVALUATED, CASE_CREATED,
    CASE_RESOLVED, APPROVAL_REQUESTED, APPROVAL_RESOLVED, and WEBHOOK_PROCESSED events.
    """
    if token:
        try:
            payload = decode_access_token(token)
            if not payload:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    broadcaster = EventBroadcaster.get_instance()
    await broadcaster.connect_websocket(websocket)

    try:
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        await broadcaster.disconnect_websocket(websocket)
    except Exception as e:
        logger.debug("WebSocket exception: %s", e)
        await broadcaster.disconnect_websocket(websocket)


@router.websocket("/ws/transactions/{user_id}")
async def websocket_user_transactions(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = Query(None),
):
    """Targeted WebSocket endpoint for a user's transaction approvals and real-time status updates."""
    if token:
        try:
            payload = decode_access_token(token)
            if not payload:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    broadcaster = EventBroadcaster.get_instance()
    await broadcaster.connect_websocket(websocket)

    try:
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        await broadcaster.disconnect_websocket(websocket)
    except Exception as e:
        logger.debug("User WebSocket exception: %s", e)
        await broadcaster.disconnect_websocket(websocket)


@router.get(
    "/stream",
    summary="Server-Sent Events (SSE) Live Event Stream",
    description="Streams real-time platform risk events and investigation alerts using standard Server-Sent Events (text/event-stream).",
)
async def sse_event_stream():
    """SSE streaming endpoint for real-time frontend monitoring."""
    broadcaster = EventBroadcaster.get_instance()
    return StreamingResponse(
        broadcaster.sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/recent",
    summary="Get Recent Platform Events",
    description="Returns the most recent in-memory security and transaction events.",
)
def get_recent_events(limit: int = 20):
    """Fetch buffered recent platform events."""
    broadcaster = EventBroadcaster.get_instance()
    return {"events": broadcaster.get_recent_events(limit=limit)}
