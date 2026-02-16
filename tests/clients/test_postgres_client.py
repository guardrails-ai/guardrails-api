"""Unit tests for guardrails_api.clients.postgres_client module."""

import unittest
from unittest.mock import patch, Mock
from guardrails_api.clients.postgres_client import postgres_is_enabled, PostgresClient


class TestPostgresIsEnabled(unittest.TestCase):
    """Test cases for the postgres_is_enabled function."""

    @patch.dict("os.environ", {}, clear=True)
    def test_postgres_disabled_by_default(self):
        """Test that postgres is disabled when PGHOST is not set."""
        result = postgres_is_enabled()
        self.assertFalse(result)

    @patch.dict("os.environ", {"PGHOST": "localhost"})
    def test_postgres_enabled_when_pghost_set(self):
        """Test that postgres is enabled when PGHOST is set."""
        result = postgres_is_enabled()
        self.assertTrue(result)

    @patch.dict("os.environ", {"PGHOST": "db.example.com"})
    def test_postgres_enabled_with_remote_host(self):
        """Test that postgres is enabled with remote host."""
        result = postgres_is_enabled()
        self.assertTrue(result)


class TestPostgresClient(unittest.TestCase):
    """Test cases for the PostgresClient class."""

    def setUp(self):
        """Reset singleton instance before each test."""
        PostgresClient._instance = None

    def test_postgres_client_is_singleton(self):
        """Test that PostgresClient implements singleton pattern."""
        client1 = PostgresClient()
        client2 = PostgresClient()
        self.assertIs(client1, client2)

    @patch.dict("os.environ", {"PGUSER": "envuser", "PGPASSWORD": "envpass"})
    def test_get_pg_creds_from_env(self):
        """Test getting PostgreSQL credentials from environment variables."""
        client = PostgresClient()
        user, password = client.get_pg_creds()

        self.assertEqual(user, "envuser")
        self.assertEqual(password, "envpass")

    @patch.dict("os.environ", {}, clear=True)
    def test_get_pg_creds_missing_raises_error(self):
        """Test that missing credentials raise RuntimeError."""
        client = PostgresClient()

        with self.assertRaises(RuntimeError) as context:
            client.get_pg_creds()

        self.assertIn("PGUSER", str(context.exception))

    def test_generate_lock_id(self):
        """Test generating lock ID from name."""
        client = PostgresClient()
        lock_id = client.generate_lock_id("test-name")

        self.assertIsInstance(lock_id, int)
        self.assertGreater(lock_id, 0)
        self.assertLess(lock_id, 2**63)

    def test_generate_lock_id_deterministic(self):
        """Test that lock ID generation is deterministic."""
        client = PostgresClient()
        lock_id1 = client.generate_lock_id("test-name")
        lock_id2 = client.generate_lock_id("test-name")

        self.assertEqual(lock_id1, lock_id2)

    def test_generate_lock_id_different_names(self):
        """Test that different names generate different lock IDs."""
        client = PostgresClient()
        lock_id1 = client.generate_lock_id("name1")
        lock_id2 = client.generate_lock_id("name2")

        self.assertNotEqual(lock_id1, lock_id2)

    @patch("guardrails_api.clients.postgres_client.postgres_is_enabled")
    def test_get_db_when_disabled(self, mock_enabled):
        """Test get_db when postgres is disabled."""
        mock_enabled.return_value = False

        client = PostgresClient()
        gen = client.get_db()
        result = next(gen)

        self.assertIsNone(result)

    @patch("guardrails_api.clients.postgres_client.postgres_is_enabled")
    def test_get_db_when_enabled(self, mock_enabled):
        """Test get_db when postgres is enabled."""
        mock_enabled.return_value = True
        mock_session = Mock()

        client = PostgresClient()
        client.SessionLocal = Mock(return_value=mock_session)

        gen = client.get_db()
        result = next(gen)

        self.assertEqual(result, mock_session)


if __name__ == "__main__":
    unittest.main()
