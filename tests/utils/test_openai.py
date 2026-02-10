"""Unit tests for guardrails_api.utils.openai module."""

import unittest
from unittest.mock import Mock
from guardrails_api.utils.openai import (
    outcome_to_stream_response,
    outcome_to_chat_completion,
)


class TestOutcomeToStreamResponse(unittest.TestCase):
    """Test cases for the outcome_to_stream_response function."""

    def test_outcome_to_stream_response_basic(self):
        """Test basic stream response conversion."""
        mock_outcome = Mock()
        mock_outcome.validated_output = "Test output"
        mock_outcome.reask = None
        mock_outcome.validation_passed = True
        mock_outcome.error = None

        result = outcome_to_stream_response(mock_outcome)

        self.assertIn("choices", result)
        self.assertIn("guardrails", result)
        self.assertEqual(result["choices"][0]["delta"]["content"], "Test output")
        self.assertTrue(result["guardrails"]["validation_passed"])
        self.assertIsNone(result["guardrails"]["reask"])
        self.assertIsNone(result["guardrails"]["error"])

    def test_outcome_to_stream_response_with_reask(self):
        """Test stream response with reask."""
        mock_outcome = Mock()
        mock_outcome.validated_output = "Output"
        mock_outcome.reask = "Please provide more details"
        mock_outcome.validation_passed = False
        mock_outcome.error = None

        result = outcome_to_stream_response(mock_outcome)

        self.assertEqual(result["guardrails"]["reask"], "Please provide more details")
        self.assertFalse(result["guardrails"]["validation_passed"])

    def test_outcome_to_stream_response_with_error(self):
        """Test stream response with error."""
        mock_outcome = Mock()
        mock_outcome.validated_output = ""
        mock_outcome.reask = None
        mock_outcome.validation_passed = False
        mock_outcome.error = "Validation error occurred"

        result = outcome_to_stream_response(mock_outcome)

        self.assertEqual(result["guardrails"]["error"], "Validation error occurred")
        self.assertFalse(result["guardrails"]["validation_passed"])


class TestOutcomeToChatCompletion(unittest.TestCase):
    """Test cases for the outcome_to_chat_completion function."""

    def test_outcome_to_chat_completion_basic(self):
        """Test basic chat completion conversion."""
        mock_outcome = Mock()
        mock_outcome.validated_output = "Test response"
        mock_outcome.reask = None
        mock_outcome.validation_passed = True
        mock_outcome.error = None
        mock_outcome.validation_summaries = []

        mock_llm_response = Mock()
        mock_llm_response.full_raw_llm_output = {
            "choices": [{"message": {"content": "original"}}]
        }

        result = outcome_to_chat_completion(
            mock_outcome, mock_llm_response, has_tool_gd_tool_call=False
        )

        self.assertIn("choices", result)
        self.assertIn("guardrails", result)
        self.assertEqual(result["choices"][0]["message"]["content"], "Test response")
        self.assertTrue(result["guardrails"]["validation_passed"])

    def test_outcome_to_chat_completion_with_tool_call(self):
        """Test chat completion with tool call."""
        mock_outcome = Mock()
        mock_outcome.validated_output = '{"key": "value"}'
        mock_outcome.reask = None
        mock_outcome.validation_passed = True
        mock_outcome.error = None
        mock_outcome.validation_summaries = []

        mock_llm_response = Mock()
        mock_llm_response.full_raw_llm_output = {
            "choices": [
                {"message": {"tool_calls": [{"function": {"arguments": "original"}}]}}
            ]
        }

        result = outcome_to_chat_completion(
            mock_outcome, mock_llm_response, has_tool_gd_tool_call=True
        )

        self.assertEqual(
            result["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"],
            '{"key": "value"}',
        )

    def test_outcome_to_chat_completion_with_validation_summaries(self):
        """Test chat completion with validation summaries."""
        mock_summary = Mock()
        mock_summary.model_dump.return_value = {
            "validator": "test_validator",
            "result": "passed",
        }

        mock_outcome = Mock()
        mock_outcome.validated_output = "Output"
        mock_outcome.reask = None
        mock_outcome.validation_passed = True
        mock_outcome.error = None
        mock_outcome.validation_summaries = [mock_summary]

        mock_llm_response = Mock()
        mock_llm_response.full_raw_llm_output = {
            "choices": [{"message": {"content": ""}}]
        }

        result = outcome_to_chat_completion(
            mock_outcome, mock_llm_response, has_tool_gd_tool_call=False
        )

        self.assertEqual(len(result["guardrails"]["validation_summaries"]), 1)
        self.assertEqual(
            result["guardrails"]["validation_summaries"][0]["validator"],
            "test_validator",
        )

    def test_outcome_to_chat_completion_without_full_raw_llm_output(self):
        """Test chat completion when llm_response lacks full_raw_llm_output."""
        mock_outcome = Mock()
        mock_outcome.validated_output = "Test"
        mock_outcome.reask = None
        mock_outcome.validation_passed = True
        mock_outcome.error = None
        mock_outcome.validation_summaries = []

        mock_llm_response = Mock(spec=[])  # No attributes

        result = outcome_to_chat_completion(
            mock_outcome, mock_llm_response, has_tool_gd_tool_call=False
        )

        self.assertIn("guardrails", result)
        self.assertEqual(result["choices"][0]["message"]["content"], "Test")

    def test_outcome_to_chat_completion_with_reask_and_error(self):
        """Test chat completion with reask and error."""
        mock_outcome = Mock()
        mock_outcome.validated_output = "Partial output"
        mock_outcome.reask = "More info needed"
        mock_outcome.validation_passed = False
        mock_outcome.error = "Validation failed"
        mock_outcome.validation_summaries = []

        mock_llm_response = Mock()
        mock_llm_response.full_raw_llm_output = {
            "choices": [{"message": {"content": ""}}]
        }

        result = outcome_to_chat_completion(
            mock_outcome, mock_llm_response, has_tool_gd_tool_call=False
        )

        self.assertEqual(result["guardrails"]["reask"], "More info needed")
        self.assertEqual(result["guardrails"]["error"], "Validation failed")
        self.assertFalse(result["guardrails"]["validation_passed"])


if __name__ == "__main__":
    unittest.main()
