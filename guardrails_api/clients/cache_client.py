import threading
from fastapi import FastAPI
from aiocache import caches, Cache
from aiocache.serializers import JsonSerializer

class CacheClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, app: FastAPI):
        caches.set_config({
            'default': {
                'cache': "aiocache.SimpleMemoryCache",
                'serializer': {
                    'class': "aiocache.serializers.JsonSerializer"
                },
                'ttl': 300
            }
        })
        self.cache = caches.get('default')

    async def get(self, key: str):
        return await self.cache.get(key)

    async def set(self, key: str, value: str, ttl: int):
        await self.cache.set(key, value, ttl=ttl)

    async def delete(self, key: str):
        await self.cache.delete(key)

    async def clear(self):
        await self.cache.clear()