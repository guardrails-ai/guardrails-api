"""Unit tests for guardrails_api.cli.cli module."""
import unittest
from guardrails_api.cli.cli import cli


class TestCLI(unittest.TestCase):
    """Test cases for the CLI module."""

    def test_cli_exists(self):
        """Test that cli object exists."""
        self.assertIsNotNone(cli)

    def test_cli_is_typer_instance(self):
        """Test that cli is a Typer instance."""
        import typer
        self.assertIsInstance(cli, typer.Typer)

    def test_cli_is_callable(self):
        """Test that cli is callable."""
        self.assertTrue(callable(cli))


if __name__ == "__main__":
    unittest.main()
