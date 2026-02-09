"""Unit tests for guardrails_api.clients.cache_client module."""
import unittest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from guardrails_api.clients.cache_client import CacheClient


class TestCacheClient(unittest.TestCase):
    """Test cases for the CacheClient class."""

    def setUp(self):
        """Reset singleton instance before each test."""
        CacheClient._instance = None

    def test_cache_client_is_singleton(self):
        """Test that CacheClient implements singleton pattern."""
        client1 = CacheClient()
        client2 = CacheClient()
        self.assertIs(client1, client2)

    def test_cache_client_thread_safe_singleton(self):
        """Test that singleton is thread-safe."""
        instances = []

        def create_instance():
            instances.append(CacheClient())

        import threading
        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All instances should be the same
        self.assertEqual(len(set(id(inst) for inst in instances)), 1)

    @patch('guardrails_api.clients.cache_client.caches')
    def test_initialize_sets_config(self, mock_caches):
        """Test that initialize sets up cache configuration."""
        mock_cache = Mock()
        mock_caches.get.return_value = mock_cache

        client = CacheClient()
        client.initialize()

        mock_caches.set_config.assert_called_once()
        config = mock_caches.set_config.call_args[0][0]
        self.assertIn("default", config)
        self.assertEqual(config["default"]["cache"], "aiocache.SimpleMemoryCache")
        self.assertEqual(config["default"]["ttl"], 300)

    @patch('guardrails_api.clients.cache_client.caches')
    def test_initialize_gets_cache(self, mock_caches):
        """Test that initialize retrieves default cache."""
        mock_cache = Mock()
        mock_caches.get.return_value = mock_cache

        client = CacheClient()
        client.initialize()

        mock_caches.get.assert_called_once_with("default")
        self.assertEqual(client.cache, mock_cache)

    @patch('guardrails_api.clients.cache_client.caches')
    def test_get_calls_cache_get(self, mock_caches):
        """Test that get method calls cache.get."""
        mock_cache = Mock()
        mock_cache.get = AsyncMock(return_value="value")
        mock_caches.get.return_value = mock_cache

        client = CacheClient()
        client.initialize()

        result = asyncio.run(client.get("test_key"))

        mock_cache.get.assert_called_once_with("test_key")
        self.assertEqual(result, "value")

    @patch('guardrails_api.clients.cache_client.caches')
    def test_set_calls_cache_set(self, mock_caches):
        """Test that set method calls cache.set with correct parameters."""
        mock_cache = Mock()
        mock_cache.set = AsyncMock()
        mock_caches.get.return_value = mock_cache

        client = CacheClient()
        client.initialize()

        asyncio.run(client.set("test_key", "test_value", 600))

        mock_cache.set.assert_called_once_with("test_key", "test_value", ttl=600)

    @patch('guardrails_api.clients.cache_client.caches')
    def test_delete_calls_cache_delete(self, mock_caches):
        """Test that delete method calls cache.delete."""
        mock_cache = Mock()
        mock_cache.delete = AsyncMock()
        mock_caches.get.return_value = mock_cache

        client = CacheClient()
        client.initialize()

        asyncio.run(client.delete("test_key"))

        mock_cache.delete.assert_called_once_with("test_key")

    @patch('guardrails_api.clients.cache_client.caches')
    def test_clear_calls_cache_clear(self, mock_caches):
        """Test that clear method calls cache.clear."""
        mock_cache = Mock()
        mock_cache.clear = AsyncMock()
        mock_caches.get.return_value = mock_cache

        client = CacheClient()
        client.initialize()

        asyncio.run(client.clear())

        mock_cache.clear.assert_called_once()


if __name__ == "__main__":
    unittest.main()
