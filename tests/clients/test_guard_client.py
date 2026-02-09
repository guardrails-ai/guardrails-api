"""Unit tests for guardrails_api.clients.guard_client module."""
import unittest
from guardrails_api.clients.guard_client import GuardClient


class TestGuardClient(unittest.TestCase):
    """Test cases for the GuardClient class."""

    def setUp(self):
        """Set up test client."""
        self.client = GuardClient()

    def test_guard_client_initialization(self):
        """Test GuardClient initialization."""
        self.assertTrue(self.client.initialized)

    def test_get_guard_raises_not_implemented(self):
        """Test that get_guard raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.client.get_guard("test_guard")

    def test_get_guard_with_as_of_date_raises_not_implemented(self):
        """Test that get_guard with as_of_date raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.client.get_guard("test_guard", as_of_date="2024-01-01")

    def test_get_guards_raises_not_implemented(self):
        """Test that get_guards raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.client.get_guards()

    def test_create_guard_raises_not_implemented(self):
        """Test that create_guard raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.client.create_guard(None)

    def test_update_guard_raises_not_implemented(self):
        """Test that update_guard raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.client.update_guard("test_guard", None)

    def test_upsert_guard_raises_not_implemented(self):
        """Test that upsert_guard raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.client.upsert_guard("test_guard", None)

    def test_delete_guard_raises_not_implemented(self):
        """Test that delete_guard raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.client.delete_guard("test_guard")

    def test_guard_client_is_base_class(self):
        """Test that GuardClient is intended as a base class."""
        # All methods should raise NotImplementedError
        methods = [
            ('get_guard', ('test',)),
            ('get_guards', ()),
            ('create_guard', (None,)),
            ('update_guard', ('test', None)),
            ('upsert_guard', ('test', None)),
            ('delete_guard', ('test',)),
        ]

        for method_name, args in methods:
            with self.subTest(method=method_name):
                method = getattr(self.client, method_name)
                with self.assertRaises(NotImplementedError):
                    method(*args)


if __name__ == "__main__":
    unittest.main()
