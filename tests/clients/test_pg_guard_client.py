"""Unit tests for guardrails_api.clients.pg_guard_client module."""
import unittest
from unittest.mock import Mock, patch
from guardrails_api.clients.pg_guard_client import PGGuardClient, from_guard_item


class TestFromGuardItem(unittest.TestCase):
    """Test cases for the from_guard_item function."""

    @patch('guardrails_api.clients.pg_guard_client.GuardStruct')
    def test_from_guard_item(self, mock_guard_struct):
        """Test converting GuardItem to GuardStruct."""
        railspec = {"name": "test", "description": "Test guard"}
        guard_item = Mock()
        guard_item.railspec = railspec

        mock_guard = Mock()
        mock_guard_struct.from_dict.return_value = mock_guard

        result = from_guard_item(guard_item)

        mock_guard_struct.from_dict.assert_called_once_with(railspec)
        self.assertEqual(result, mock_guard)


class TestPGGuardClient(unittest.TestCase):
    """Test cases for the PGGuardClient class."""

    @patch('guardrails_api.clients.pg_guard_client.PostgresClient')
    def test_pg_guard_client_initialization(self, mock_pg_client):
        """Test PGGuardClient initialization."""
        mock_client_instance = Mock()
        mock_pg_client.return_value = mock_client_instance

        client = PGGuardClient()

        self.assertTrue(client.initialized)
        self.assertEqual(client.pgClient, mock_client_instance)

    @patch('guardrails_api.clients.pg_guard_client.PostgresClient')
    def test_get_db_context(self, mock_pg_client):
        """Test get_db_context context manager."""
        mock_session = Mock()
        mock_client_instance = Mock()
        mock_client_instance.SessionLocal.return_value = mock_session
        mock_pg_client.return_value = mock_client_instance

        client = PGGuardClient()

        with client.get_db_context() as db:
            self.assertEqual(db, mock_session)

        mock_session.close.assert_called_once()

    @patch('guardrails_api.clients.pg_guard_client.PostgresClient')
    def test_util_get_guard_item(self, mock_pg_client):
        """Test util_get_guard_item retrieves guard from database."""
        mock_db = Mock()
        mock_guard_item = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_guard_item

        client = PGGuardClient()
        result = client.util_get_guard_item("test_guard", mock_db)

        self.assertEqual(result, mock_guard_item)
        mock_db.query.assert_called_once()

    @patch('guardrails_api.clients.pg_guard_client.from_guard_item')
    @patch('guardrails_api.clients.pg_guard_client.GuardItem')
    @patch('guardrails_api.clients.pg_guard_client.PostgresClient')
    def test_util_create_guard(self, mock_pg_client, mock_guard_item_class, mock_from_guard_item):
        """Test util_create_guard creates guard in database."""
        mock_db = Mock()
        mock_guard = Mock()
        mock_guard.name = "test_guard"
        mock_guard.description = "Test description"
        mock_guard.to_dict.return_value = {"name": "test_guard"}

        mock_guard_item = Mock()
        mock_guard_item_class.return_value = mock_guard_item

        mock_result = Mock()
        mock_from_guard_item.return_value = mock_result

        client = PGGuardClient()
        result = client.util_create_guard(mock_guard, mock_db)

        mock_db.add.assert_called_once_with(mock_guard_item)
        mock_db.commit.assert_called_once()
        mock_from_guard_item.assert_called_once_with(mock_guard_item)
        self.assertEqual(result, mock_result)

    @patch('guardrails_api.clients.pg_guard_client.PostgresClient')
    def test_get_guard_method_exists(self, mock_pg_client):
        """Test that get_guard method exists."""
        client = PGGuardClient()
        self.assertTrue(hasattr(client, 'get_guard'))
        self.assertTrue(callable(client.get_guard))


if __name__ == "__main__":
    unittest.main()
