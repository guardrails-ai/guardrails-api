"""Unit tests for guardrails_api.cli module."""

import unittest
import typer
from unittest.mock import patch


class TestVersionCallback(unittest.TestCase):
    @patch("builtins.print")
    @patch(
        "guardrails_api.cli.__init__.importlib.metadata.version", return_value="0.X.0"
    )
    def test_version_callback_with_true(self, mock_importlib, mock_print):
        """Test that cli object exists."""
        from guardrails_api.cli import version_callback

        with self.assertRaises(typer.Exit):
            version_callback(True)

        self.assertEqual(
            mock_print.call_args[0][0], "guardrails-api CLI Version: 0.X.0"
        )

        self.assertEqual(mock_importlib.call_count, 1)

    @patch("builtins.print")
    @patch(
        "guardrails_api.cli.__init__.importlib.metadata.version", return_value="0.X.0"
    )
    def test_version_callback_with_false(self, mock_importlib, mock_print):
        """Test that cli object exists."""
        from guardrails_api.cli import version_callback

        version_callback(False)

        self.assertEqual(mock_print.call_count, 0)

        self.assertEqual(mock_importlib.call_count, 0)
