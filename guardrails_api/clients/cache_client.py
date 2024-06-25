from flask_caching import Cache


# TODO: Add option to connect to Redis or MemCached backend with environment variables
class CacheClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheClient, cls).__new__(cls)
        return cls._instance

    def initialize(self, app):
        self.cache = Cache(
            app,
            config={
                "CACHE_TYPE": "SimpleCache",
                "CACHE_DEFAULT_TIMEOUT": 300,
                "CACHE_THRESHOLD": 50,
            },
        )

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value, ttl):
        self.cache.set(key, value, timeout=ttl)

    def delete(self, key):
        self.cache.delete(key)

    def clear(self):
        self.cache.clear()
