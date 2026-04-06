import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        # user_id -> list of WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket):
        """Register new connection"""
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []

            self.active_connections[user_id].append(websocket)
            logger.info(
                f"User {user_id} connected (total connections: {len(self.active_connections[user_id])})"
            )

    async def disconnect(self, user_id: int, websocket: WebSocket = None):
        """Remove connection"""
        async with self._lock:
            if user_id in self.active_connections:
                if websocket and websocket in self.active_connections[user_id]:
                    # Remove specific connection
                    self.active_connections[user_id].remove(websocket)
                elif not websocket:
                    # Remove all connections for user
                    self.active_connections[user_id] = []

                # Clean up empty lists
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

                logger.info(f"User {user_id} disconnected")

    async def send_personal_message(self, user_id: int, message: dict):
        """Send message to specific user (all their connections)"""
        # We need to copy to avoid modifying while iterating
        if user_id in self.active_connections:
            connections = list(self.active_connections[user_id])
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
                    await self.disconnect(user_id, connection)


class WebSocketRateLimiter:
    """Rate limit WebSocket messages"""

    def __init__(self, max_messages: int = 10, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.message_history: Dict[int, List[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to send message"""
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.window_seconds)

            # Remove old timestamps
            self.message_history[user_id] = [
                ts for ts in self.message_history[user_id] if ts > cutoff
            ]

            # Check limit
            if len(self.message_history[user_id]) >= self.max_messages:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                return False

            # Add current timestamp
            self.message_history[user_id].append(now)
            return True


# Global instances
connection_manager = ConnectionManager()
rate_limiter = WebSocketRateLimiter(max_messages=20, window_seconds=60)
