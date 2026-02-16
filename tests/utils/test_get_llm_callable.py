"""Unit tests for guardrails_api.utils.get_llm_callable module."""

import unittest
from unittest.mock import patch, Mock
from guardrails_api.utils.get_llm_callable import get_llm_callable


class TestGetLLMCallable(unittest.TestCase):
    """Test cases for the get_llm_callable function."""

    @patch("guardrails_api.utils.get_llm_callable.litellm")
    @patch("guardrails_api.utils.get_llm_callable.LLMResource")
    def test_get_llm_callable_litellm_completion(self, mock_llm_resource, mock_litellm):
        """Test getting litellm.completion callable."""
        mock_llm_resource.LITELLM_DOT_COMPLETION.value = "litellm.completion"
        mock_litellm.completion = Mock()

        result = get_llm_callable("litellm.completion")

        self.assertEqual(result, mock_litellm.completion)

    @patch("guardrails_api.utils.get_llm_callable.litellm")
    @patch("guardrails_api.utils.get_llm_callable.LLMResource")
    def test_get_llm_callable_litellm_acompletion(
        self, mock_llm_resource, mock_litellm
    ):
        """Test getting litellm.acompletion callable."""
        mock_llm_resource.LITELLM_DOT_ACOMPLETION.value = "litellm.acompletion"
        mock_litellm.acompletion = Mock()

        result = get_llm_callable("litellm.acompletion")

        self.assertEqual(result, mock_litellm.acompletion)

    @patch("guardrails_api.utils.get_llm_callable.litellm")
    @patch("guardrails_api.utils.get_llm_callable.LLMResource")
    def test_get_llm_callable_unknown_api(self, mock_llm_resource, mock_litellm):
        """Test get_llm_callable with unknown API returns None."""
        mock_llm_resource.LITELLM_DOT_COMPLETION.value = "litellm.completion"
        mock_llm_resource.LITELLM_DOT_ACOMPLETION.value = "litellm.acompletion"

        result = get_llm_callable("unknown.api")

        self.assertIsNone(result)

    @patch("guardrails_api.utils.get_llm_callable.litellm")
    @patch("guardrails_api.utils.get_llm_callable.LLMResource")
    def test_get_llm_callable_empty_string(self, mock_llm_resource, mock_litellm):
        """Test get_llm_callable with empty string."""
        mock_llm_resource.LITELLM_DOT_COMPLETION.value = "litellm.completion"
        mock_llm_resource.LITELLM_DOT_ACOMPLETION.value = "litellm.acompletion"

        result = get_llm_callable("")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
