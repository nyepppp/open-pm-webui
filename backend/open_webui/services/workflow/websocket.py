"""
Workflow WebSocket Streaming Service

Provides real-time streaming of workflow execution progress via WebSocket.
Integrates with OpenWebUI's existing Socket.IO infrastructure.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from open_webui.socket.main import sio, enter_room_for_users
from open_webui.pm.models.workflow import WorkflowExecutions

logger = logging.getLogger(__name__)


class WorkflowWebSocketManager:
    """
    Manages WebSocket connections for workflow execution streaming.

    Provides real-time updates on:
    - Node execution status
    - Execution progress
    - Error notifications
    - Completion events
    """

    def __init__(self):
        self._active_streams: Dict[str, Dict[str, Any]] = {}
        self._execution_listeners: Dict[str, List[Callable]] = {}

    async def start_stream(self, execution_id: str, user_id: Optional[str] = None) -> str:
        """
        Start a new WebSocket stream for a workflow execution.

        Args:
            execution_id: The workflow execution ID
            user_id: Optional user ID for targeted updates

        Returns:
            Stream ID
        """
        stream_id = f"workflow:{execution_id}"

        self._active_streams[stream_id] = {
            "execution_id": execution_id,
            "user_id": user_id,
            "started_at": datetime.utcnow().isoformat(),
            "status": "active"
        }

        # 让发起执行的用户加入此 stream 房间，以便接收实时事件
        if user_id:
            try:
                await enter_room_for_users(stream_id, [user_id])
            except Exception as e:
                logger.error(f"Failed to enter room for user {user_id}: {e}")

        # Emit stream start event
        await self._emit_event(stream_id, {
            "event": "stream.started",
            "execution_id": execution_id,
            "timestamp": datetime.utcnow().isoformat()
        })

        return stream_id
    
    async def emit_node_start(self, execution_id: str, node_id: str, node_type: str, node_name: str = None):
        """
        Emit a node start event.
        
        Args:
            execution_id: The workflow execution ID
            node_id: The node ID
            node_type: The node type
            node_name: Optional node name
        """
        await self._emit_event(f"workflow:{execution_id}", {
            "event": "node.started",
            "execution_id": execution_id,
            "node_id": node_id,
            "node_type": node_type,
            "node_name": node_name,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def emit_node_complete(self, execution_id: str, node_id: str, node_type: str, 
                                  output: Optional[Dict] = None, execution_time_ms: Optional[float] = None):
        """
        Emit a node completion event.
        
        Args:
            execution_id: The workflow execution ID
            node_id: The node ID
            node_type: The node type
            output: Optional node output data
            execution_time_ms: Optional execution time in milliseconds
        """
        await self._emit_event(f"workflow:{execution_id}", {
            "event": "node.completed",
            "execution_id": execution_id,
            "node_id": node_id,
            "node_type": node_type,
            "output": output,
            "execution_time_ms": execution_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def emit_node_error(self, execution_id: str, node_id: str, node_type: str, error: str):
        """
        Emit a node error event.
        
        Args:
            execution_id: The workflow execution ID
            node_id: The node ID
            node_type: The node type
            error: Error message
        """
        await self._emit_event(f"workflow:{execution_id}", {
            "event": "node.error",
            "execution_id": execution_id,
            "node_id": node_id,
            "node_type": node_type,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def emit_execution_progress(self, execution_id: str, progress: float, 
                                       total_nodes: int, completed_nodes: int):
        """
        Emit execution progress event.
        
        Args:
            execution_id: The workflow execution ID
            progress: Progress percentage (0-100)
            total_nodes: Total number of nodes
            completed_nodes: Number of completed nodes
        """
        await self._emit_event(f"workflow:{execution_id}", {
            "event": "execution.progress",
            "execution_id": execution_id,
            "progress": progress,
            "total_nodes": total_nodes,
            "completed_nodes": completed_nodes,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def emit_execution_complete(self, execution_id: str, status: str, 
                                       output_data: Optional[Dict] = None, 
                                       error_message: Optional[str] = None):
        """
        Emit execution completion event.
        
        Args:
            execution_id: The workflow execution ID
            status: Final execution status
            output_data: Optional output data
            error_message: Optional error message
        """
        await self._emit_event(f"workflow:{execution_id}", {
            "event": "execution.completed",
            "execution_id": execution_id,
            "status": status,
            "output_data": output_data,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def emit_log(self, execution_id: str, level: str, message: str, 
                       node_id: Optional[str] = None):
        """
        Emit a log event.
        
        Args:
            execution_id: The workflow execution ID
            level: Log level (info, warning, error, debug)
            message: Log message
            node_id: Optional node ID
        """
        await self._emit_event(f"workflow:{execution_id}", {
            "event": "log",
            "execution_id": execution_id,
            "node_id": node_id,
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def end_stream(self, execution_id: str):
        """
        End a WebSocket stream.
        
        Args:
            execution_id: The workflow execution ID
        """
        stream_id = f"workflow:{execution_id}"
        
        if stream_id in self._active_streams:
            await self._emit_event(stream_id, {
                "event": "stream.ended",
                "execution_id": execution_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            del self._active_streams[stream_id]
    
    async def _emit_event(self, stream_id: str, data: Dict[str, Any]):
        """
        Emit an event to all connected clients.
        
        Args:
            stream_id: The stream ID
            data: Event data
        """
        try:
            # Emit to the workflow room
            await sio.emit("workflow:event", data, room=stream_id)
        except Exception as e:
            logger.error(f"Failed to emit WebSocket event: {e}")
    
    def get_stream_status(self, execution_id: str) -> Optional[Dict]:
        """
        Get the status of a stream.
        
        Args:
            execution_id: The workflow execution ID
            
        Returns:
            Stream status or None
        """
        stream_id = f"workflow:{execution_id}"
        return self._active_streams.get(stream_id)
    
    def is_stream_active(self, execution_id: str) -> bool:
        """
        Check if a stream is active.
        
        Args:
            execution_id: The workflow execution ID
            
        Returns:
            True if the stream is active
        """
        stream_id = f"workflow:{execution_id}"
        return stream_id in self._active_streams


# Singleton instance
workflow_websocket_manager = WorkflowWebSocketManager()
