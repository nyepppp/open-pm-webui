"""Timbal API client for Python backend."""

import asyncio
import httpx
import os
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime, timezone
import json

from .models import TimbalWorkflow, TimbalExecution, TimbalConfig


class TimbalClientError(Exception):
    """Base exception for Timbal client errors."""
    pass


class TimbalServiceError(TimbalClientError):
    """Exception for Timbal service errors."""
    pass


class TimbalClient:
    """HTTP client for Timbal API."""
    
    def __init__(self, config: TimbalConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.endpoint_url,
            timeout=config.timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def healthcheck(self) -> Dict[str, Any]:
        """Check Timbal service health."""
        try:
            response = await self.client.get("/healthcheck")
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise TimbalServiceError("Healthcheck timed out - service unavailable")
        except httpx.HTTPError as e:
            raise TimbalServiceError(f"Healthcheck failed: {e}")
    
    async def run_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any],
        sync: bool = False
    ) -> TimbalExecution:
        """Execute a workflow."""
        try:
            response = await self.client.post(
                "/run",
                json={
                    "workflow_id": workflow_id,
                    "inputs": inputs,
                    "sync": sync
                }
            )
            response.raise_for_status()
            data = response.json()
            return TimbalExecution(**data)
        except httpx.TimeoutException:
            raise TimbalServiceError("Workflow execution timed out")
        except httpx.HTTPError as e:
            raise TimbalServiceError(f"Workflow execution failed: {e}")
    
    async def stream_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a workflow with SSE streaming."""
        try:
            async with self.client.stream(
                "POST",
                "/stream",
                json={
                    "workflow_id": workflow_id,
                    "inputs": inputs
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        yield data
        except httpx.TimeoutException:
            raise TimbalServiceError("Workflow streaming timed out")
        except httpx.HTTPError as e:
            raise TimbalServiceError(f"Workflow streaming failed: {e}")
    
    async def get_execution(self, execution_id: str) -> TimbalExecution:
        """Get execution status."""
        try:
            response = await self.client.get(f"/executions/{execution_id}")
            response.raise_for_status()
            data = response.json()
            return TimbalExecution(**data)
        except httpx.TimeoutException:
            raise TimbalServiceError("Get execution timed out")
        except httpx.HTTPError as e:
            raise TimbalServiceError(f"Get execution failed: {e}")
    
    async def stop_execution(self, execution_id: str) -> TimbalExecution:
        """Stop a running execution."""
        try:
            response = await self.client.post(f"/executions/{execution_id}/stop")
            response.raise_for_status()
            data = response.json()
            return TimbalExecution(**data)
        except httpx.TimeoutException:
            raise TimbalServiceError("Stop execution timed out")
        except httpx.HTTPError as e:
            raise TimbalServiceError(f"Stop execution failed: {e}")


class TimbalClientWithRetry(TimbalClient):
    """Timbal client with exponential backoff retry."""
    
    def __init__(self, config: TimbalConfig):
        super().__init__(config)
        self.max_retries = config.max_retries
        self.retry_intervals = config.retry_intervals
    
    async def _retry_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Execute request with retry logic."""
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPError as e:
                if attempt >= self.max_retries:
                    raise TimbalServiceError(f"Request failed after {self.max_retries} retries: {e}")
                
                wait_time = self.retry_intervals[min(attempt, len(self.retry_intervals) - 1)]
                await asyncio.sleep(wait_time)
        
        # This line should never be reached, but satisfies type checker
        raise RuntimeError("Unexpected end of retry loop")
    
    async def run_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any],
        sync: bool = False
    ) -> TimbalExecution:
        """Execute a workflow with retry."""
        response = await self._retry_request(
            "POST",
            "/run",
            json={
                "workflow_id": workflow_id,
                "inputs": inputs,
                "sync": sync
            }
        )
        data = response.json()
        return TimbalExecution(**data)
