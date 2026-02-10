"""Unit tests for guardrails_api.app module."""
import unittest
from guardrails_api import app


class TestAppModule(unittest.TestCase):
    """Test cases for the app module."""

    def test_app_module_exists(self):
        """Test that app module can be imported."""
        self.assertIsNotNone(app)

    def test_app_module_has_create_app(self):
        """Test that app module has create_app function."""
        self.assertTrue(hasattr(app, 'create_app'))

    def test_create_app_is_callable(self):
        """Test that create_app is callable."""
        self.assertTrue(callable(app.create_app))

    def test_create_app_function_signature(self):
        """Test that create_app function has correct signature."""
        import inspect
        sig = inspect.signature(app.create_app)
        self.assertIsInstance(sig, inspect.Signature)
        # create_app should be callable
        self.assertTrue(callable(app.create_app))
        # Verify it's a function
        self.assertTrue(inspect.isfunction(app.create_app))


if __name__ == "__main__":
    unittest.main()
