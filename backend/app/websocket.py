"""
WebSocket Live Connection Manager
"""

import json
import logging
from typing import List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("backend_ws")


class ConnectionManager:
    """Manages active dashboard WebSocket subscriptions."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active subscribers: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active subscribers: {len(self.active_connections)}")

    async def broadcast(self, message_type: str, data: dict):
        """Broadcasts structured event to all connected dashboard clients."""
        if not self.active_connections:
            return

        payload = json.dumps({"type": message_type, "data": data})
        dead_sockets = []

        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Failed to send to client ({e}). Marking for removal.")
                dead_sockets.append(connection)

        for s in dead_sockets:
            self.disconnect(s)


ws_manager = ConnectionManager()
