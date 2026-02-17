import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

from fastapi import WebSocket

class LogManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.history: List[Dict[str, Any]] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send history upon connection if needed
        # for log in self.history:
        #     await websocket.send_json(log)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        self.history.append(message)
        # Keep history manageable
        if len(self.history) > 100:
            self.history.pop(0)
            
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Handle broken connections generally by removing them in disconnect
                pass

    async def log(self, step: str, status: str, details: str, latency: float = 0.0):
        """
        Log an event to the frontend.
        step: The processing step (e.g., "Input Guard", "LLM", "Output Guard")
        status: "start", "success", "error", "processing"
        details: Description of what's happening
        """
        message = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,
            "details": details,
            "latency": latency
        }
        # Print to console for debugging
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{step.upper()}] [{status.upper()}] {details}")
        await self.broadcast(message)

# Global instance
log_manager = LogManager()
