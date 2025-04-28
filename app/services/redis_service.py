import redis.asyncio as redis
from app.config import REDIS_URL
import json
from typing import Optional


class RedisService:
    def __init__(self):
        self.connection = redis.from_url(REDIS_URL)
            
    async def set(self, key: str, value: dict, ex: Optional[str] = None):
        await self.connection.set(key,  json.dumps(value), ex=ex)
        
    async def get(self, key: str)-> Optional[dict]:
        data = self.connection.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def delete(self, key: str):
        await self.connection.delete(key)