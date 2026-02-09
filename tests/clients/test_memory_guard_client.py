"""Unit tests for guardrails_api.clients.memory_guard_client module."""
import unittest
from unittest.mock import Mock
from guardrails_api.clients.memory_guard_client import MemoryGuardClient
from guardrails_api.classes.http_error import HttpError


class TestMemoryGuardClient(unittest.TestCase):
    """Test cases for the MemoryGuardClient class."""

    def setUp(self):
        """Set up test client and clear guards."""
        self.client = MemoryGuardClient()
        self.client.guards = {}  # Clear guards before each test

    def test_memory_guard_client_initialization(self):
        """Test MemoryGuardClient initialization."""
        self.assertTrue(self.client.initialized)
        self.assertIsInstance(self.client.guards, dict)

    def test_create_guard(self):
        """Test creating a guard."""
        mock_guard = Mock()
        mock_guard.name = "test_guard"

        result = self.client.create_guard(mock_guard)

        self.assertEqual(result, mock_guard)
        self.assertIn("test_guard", self.client.guards)
        self.assertEqual(self.client.guards["test_guard"], mock_guard)

    def test_get_guard_existing(self):
        """Test getting an existing guard."""
        mock_guard = Mock()
        mock_guard.name = "test_guard"
        self.client.guards["test_guard"] = mock_guard

        result = self.client.get_guard("test_guard")

        self.assertEqual(result, mock_guard)

    def test_get_guard_non_existing(self):
        """Test getting a non-existing guard returns None."""
        result = self.client.get_guard("non_existing")

        self.assertIsNone(result)

    def test_get_guard_with_as_of_date(self):
        """Test that as_of_date parameter is accepted but not used."""
        mock_guard = Mock()
        mock_guard.name = "test_guard"
        self.client.guards["test_guard"] = mock_guard

        result = self.client.get_guard("test_guard", as_of_date="2024-01-01")

        self.assertEqual(result, mock_guard)

    def test_get_guards_empty(self):
        """Test getting guards when none exist."""
        result = self.client.get_guards()

        self.assertEqual(result, [])

    def test_get_guards_multiple(self):
        """Test getting multiple guards."""
        mock_guard1 = Mock()
        mock_guard1.name = "guard1"
        mock_guard2 = Mock()
        mock_guard2.name = "guard2"

        self.client.guards["guard1"] = mock_guard1
        self.client.guards["guard2"] = mock_guard2

        result = self.client.get_guards()

        self.assertEqual(len(result), 2)
        self.assertIn(mock_guard1, result)
        self.assertIn(mock_guard2, result)

    def test_update_guard_existing(self):
        """Test updating an existing guard."""
        old_guard = Mock()
        old_guard.name = "test_guard"
        new_guard = Mock()
        new_guard.name = "test_guard"

        self.client.guards["test_guard"] = old_guard

        result = self.client.update_guard("test_guard", new_guard)

        self.assertEqual(result, new_guard)
        self.assertEqual(self.client.guards["test_guard"], new_guard)

    def test_update_guard_non_existing_raises_error(self):
        """Test updating a non-existing guard raises HttpError."""
        new_guard = Mock()
        new_guard.name = "test_guard"

        with self.assertRaises(HttpError) as context:
            self.client.update_guard("test_guard", new_guard)

        error = context.exception
        self.assertEqual(error.status, 404)
        self.assertEqual(error.message, "NotFound")

    def test_upsert_guard(self):
        """Test upserting a guard."""
        mock_guard = Mock()
        mock_guard.name = "test_guard"

        result = self.client.upsert_guard("test_guard", mock_guard)

        self.assertEqual(result, mock_guard)
        self.assertIn("test_guard", self.client.guards)

    def test_upsert_guard_overwrites_existing(self):
        """Test that upsert overwrites existing guard."""
        old_guard = Mock()
        old_guard.name = "test_guard"
        new_guard = Mock()
        new_guard.name = "test_guard"

        self.client.guards["test_guard"] = old_guard

        result = self.client.upsert_guard("test_guard", new_guard)

        self.assertEqual(result, new_guard)
        self.assertEqual(self.client.guards["test_guard"], new_guard)

    def test_delete_guard_existing(self):
        """Test deleting an existing guard."""
        mock_guard = Mock()
        mock_guard.name = "test_guard"
        self.client.guards["test_guard"] = mock_guard

        result = self.client.delete_guard("test_guard")

        self.assertEqual(result, mock_guard)
        self.assertNotIn("test_guard", self.client.guards)

    def test_delete_guard_non_existing_raises_error(self):
        """Test deleting a non-existing guard raises HttpError."""
        with self.assertRaises(HttpError) as context:
            self.client.delete_guard("non_existing")

        error = context.exception
        self.assertEqual(error.status, 404)
        self.assertEqual(error.message, "NotFound")

    def test_guards_dict_is_shared(self):
        """Test that guards dict is shared across instances."""
        client1 = MemoryGuardClient()
        client2 = MemoryGuardClient()

        mock_guard = Mock()
        mock_guard.name = "shared_guard"
        client1.create_guard(mock_guard)

        # Both clients should see the same guard
        self.assertEqual(client2.get_guard("shared_guard"), mock_guard)


if __name__ == "__main__":
    unittest.main()
