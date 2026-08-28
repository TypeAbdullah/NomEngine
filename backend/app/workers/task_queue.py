"""
Task Queue Abstraction
Provides async task producer/consumer model with Redis List or in-memory asyncio.Queue.
"""
import asyncio
import json
from typing import Any, Dict, Optional
from app.cache.redis_cache import cache_service
from app.monitoring.logger import logger


class TaskQueue:
    """Distributed task queue supporting Redis and async memory queues."""

    def __init__(self, queue_name: str = "nomengine_tasks"):
        self.queue_name = queue_name
        self._memory_queue: asyncio.Queue = asyncio.Queue()

    async def enqueue(self, task_type: str, payload: Dict[str, Any]):
        """Pushes a task into the queue."""
        task_data = {"type": task_type, "payload": payload}
        try:
            if cache_service.is_connected and cache_service.redis_client:
                await cache_service.redis_client.rpush(
                    self.queue_name, json.dumps(task_data)
                )
            else:
                await self._memory_queue.put(task_data)
        except Exception as e:
            logger.error(f"Failed to enqueue task: {e}")
            await self._memory_queue.put(task_data)

    async def dequeue(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Pulls the next task from the queue."""
        try:
            if cache_service.is_connected and cache_service.redis_client:
                res = await cache_service.redis_client.blpop(self.queue_name, timeout=int(timeout) or 1)
                if res:
                    _, data_str = res
                    return json.loads(data_str)
            else:
                try:
                    return await asyncio.wait_for(self._memory_queue.get(), timeout=timeout)
                except asyncio.TimeoutError:
                    return None
        except Exception as e:
            logger.debug(f"Queue dequeue timeout or error: {e}")
            return None


task_queue = TaskQueue()
