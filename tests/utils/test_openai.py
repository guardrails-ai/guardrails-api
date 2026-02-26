"""Unit tests for guardrails_api.utils.openai module."""

import asyncio
import json
import unittest
from unittest.mock import Mock, patch

from guardrails_api.utils.openai import (
    guarded_chat_completion,
    guarded_chat_completion_stream,
)


class TestGuardedChatCompletion(unittest.TestCase):
    """Test cases for guarded_chat_completion function."""

    def _make_mock_model_response(self, content="Hello!"):
        """Create a mock litellm ModelResponse."""
        mock_response = Mock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"content": content}}],
            "model": "gpt-4",
        }
        mock_choice = Mock()
        mock_choice.message.content = content
        mock_choice.message.function_call = None
        mock_choice.message.tool_calls = None
        mock_response.choices = [mock_choice]
        return mock_response

    def _make_fake_guard(self, mock_outcome):
        """Create a mock guard that calls llm_api and returns mock_outcome."""
        mock_guard = Mock()

        def fake_guard_call(*args, **kwargs):
            llm_api = kwargs.get("llm_api")
            if llm_api:
                llm_api(messages=kwargs.get("messages", []))
            return mock_outcome

        mock_guard.side_effect = fake_guard_call
        return mock_guard

    def test_returns_dict_with_guardrails_key(self):
        """Test guarded_chat_completion returns dict containing guardrails key."""
        mock_model_response = self._make_mock_model_response(content="Hello!")
        mock_outcome = Mock()
        mock_outcome.model_dump.return_value = {
            "validation_passed": True,
            "validated_output": "Hello!",
        }
        mock_guard = self._make_fake_guard(mock_outcome)

        with patch(
            "guardrails_api.utils.openai.litellm.completion",
            return_value=mock_model_response,
        ):
            result = asyncio.run(
                guarded_chat_completion(
                    mock_guard,
                    {"messages": [{"role": "user", "content": "Hello"}]},
                )
            )

        self.assertIn("guardrails", result)
        self.assertIn("choices", result)
        self.assertTrue(result["guardrails"]["validation_passed"])

    def test_guard_called_with_num_reasks_zero(self):
        """Test guard is always called with num_reasks=0."""
        mock_model_response = self._make_mock_model_response()
        mock_outcome = Mock()
        mock_outcome.model_dump.return_value = {"validation_passed": True}
        mock_guard = self._make_fake_guard(mock_outcome)

        with patch(
            "guardrails_api.utils.openai.litellm.completion",
            return_value=mock_model_response,
        ):
            asyncio.run(
                guarded_chat_completion(
                    mock_guard,
                    {"messages": [{"role": "user", "content": "Test"}]},
                )
            )

        call_kwargs = mock_guard.call_args[1]
        self.assertEqual(call_kwargs["num_reasks"], 0)

    def test_llm_wrapper_extracts_content_from_message(self):
        """Test llm_wrapper extracts content from message.content."""
        mock_model_response = self._make_mock_model_response(
            content="Extracted content"
        )
        mock_outcome = Mock()
        mock_outcome.model_dump.return_value = {"validation_passed": True}
        captured_output = []

        mock_guard = Mock()

        def fake_guard_call(*args, **kwargs):
            llm_api = kwargs.get("llm_api")
            if llm_api:
                output = llm_api(messages=kwargs.get("messages", []))
                captured_output.append(output)
            return mock_outcome

        mock_guard.side_effect = fake_guard_call

        with patch(
            "guardrails_api.utils.openai.litellm.completion",
            return_value=mock_model_response,
        ):
            asyncio.run(
                guarded_chat_completion(
                    mock_guard,
                    {"messages": [{"role": "user", "content": "Hello"}]},
                )
            )

        self.assertEqual(len(captured_output), 1)
        self.assertEqual(captured_output[0], "Extracted content")

    def test_llm_wrapper_extracts_function_call_arguments(self):
        """Test llm_wrapper extracts function_call.arguments when content is None."""
        mock_model_response = Mock()
        mock_model_response.model_dump.return_value = {
            "choices": [
                {"message": {"function_call": {"arguments": '{"key": "val"}'}}}
            ],
            "model": "gpt-4",
        }
        mock_choice = Mock()
        mock_choice.message.content = None
        mock_choice.message.function_call = Mock()
        mock_choice.message.function_call.arguments = '{"key": "val"}'
        mock_choice.message.tool_calls = None
        mock_model_response.choices = [mock_choice]

        mock_outcome = Mock()
        mock_outcome.model_dump.return_value = {"validation_passed": True}
        captured_output = []

        mock_guard = Mock()

        def fake_guard_call(*args, **kwargs):
            llm_api = kwargs.get("llm_api")
            if llm_api:
                output = llm_api(messages=[])
                captured_output.append(output)
            return mock_outcome

        mock_guard.side_effect = fake_guard_call

        with patch(
            "guardrails_api.utils.openai.litellm.completion",
            return_value=mock_model_response,
        ):
            asyncio.run(guarded_chat_completion(mock_guard, {"messages": []}))

        self.assertEqual(captured_output[0], '{"key": "val"}')

    def test_llm_wrapper_extracts_tool_call_arguments(self):
        """Test llm_wrapper extracts tool_calls arguments when content and function_call are None."""
        mock_tool_call = Mock()
        mock_tool_call.function.arguments = '{"tool": "args"}'

        mock_model_response = Mock()
        mock_model_response.model_dump.return_value = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [{"function": {"arguments": '{"tool": "args"}'}}]
                    }
                }
            ],
            "model": "gpt-4",
        }
        mock_choice = Mock()
        mock_choice.message.content = None
        mock_choice.message.function_call = None
        mock_choice.message.tool_calls = [mock_tool_call]
        mock_model_response.choices = [mock_choice]

        mock_outcome = Mock()
        mock_outcome.model_dump.return_value = {"validation_passed": True}
        captured_output = []

        mock_guard = Mock()

        def fake_guard_call(*args, **kwargs):
            llm_api = kwargs.get("llm_api")
            if llm_api:
                output = llm_api(messages=[])
                captured_output.append(output)
            return mock_outcome

        mock_guard.side_effect = fake_guard_call

        with patch(
            "guardrails_api.utils.openai.litellm.completion",
            return_value=mock_model_response,
        ):
            asyncio.run(guarded_chat_completion(mock_guard, {"messages": []}))

        self.assertEqual(captured_output[0], '{"tool": "args"}')


class TestGuardedChatCompletionStream(unittest.TestCase):
    """Test cases for guarded_chat_completion_stream function."""

    def _make_mock_stream_chunk(self, content="Hello"):
        """Create a mock streaming chunk."""
        mock_chunk = Mock()
        mock_chunk.model_dump.return_value = {
            "choices": [{"delta": {"content": content}}],
        }
        mock_delta = Mock()
        mock_delta.content = content
        mock_delta.function_call = None
        mock_delta.tool_calls = None
        mock_choice = Mock()
        mock_choice.delta = mock_delta
        mock_chunk.choices = [mock_choice]
        return mock_chunk

    def _make_fake_stream_guard(self, mock_outcome):
        """Create a mock guard that calls llm_api (consuming one chunk) and yields mock_outcome."""
        mock_guard = Mock()
        mock_guard.history = Mock()
        mock_guard.history.last = Mock()
        mock_guard.history.last.validator_logs = []

        def fake_stream_call(*args, **kwargs):
            llm_api = kwargs.get("llm_api")
            if llm_api:
                gen = llm_api(messages=kwargs.get("messages", []))
                try:
                    next(gen)
                except StopIteration:
                    pass
            yield mock_outcome

        mock_guard.side_effect = fake_stream_call
        return mock_guard

    def test_returns_iterable_of_sse_strings(self):
        """Test guarded_chat_completion_stream returns iterable SSE strings."""
        mock_chunk = self._make_mock_stream_chunk(content="Hello")
        mock_outcome = Mock()
        mock_outcome.model_dump.return_value = {"validation_passed": True}
        mock_outcome.validation_summaries = [Mock()]

        mock_guard = self._make_fake_stream_guard(mock_outcome)

        with patch(
            "guardrails_api.utils.openai.litellm.completion",
            side_effect=lambda *args, **kwargs: iter([mock_chunk]),
        ):
            result = asyncio.run(
                guarded_chat_completion_stream(
                    mock_guard,
                    {"messages": [{"role": "user", "content": "Hello"}]},
                )
            )
            # Must consume generator inside patch context since it's lazy
            chunks = list(result)

        self.assertIsNotNone(result)
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIsInstance(chunk, str)
            if chunk != "\n":
                self.assertTrue(
                    chunk.startswith("data: "),
                    f"Expected SSE data format, got: {chunk!r}",
                )

    def test_stream_chunks_contain_guardrails_key(self):
        """Test that stream chunks include guardrails data."""
        mock_chunk = self._make_mock_stream_chunk(content="Test")
        mock_outcome = Mock()
        mock_outcome.model_dump.return_value = {
            "validation_passed": True,
            "validated_output": "Test",
        }
        mock_outcome.validation_summaries = [Mock()]

        mock_guard = self._make_fake_stream_guard(mock_outcome)

        with patch(
            "guardrails_api.utils.openai.litellm.completion",
            side_effect=lambda *args, **kwargs: iter([mock_chunk]),
        ):
            result = asyncio.run(
                guarded_chat_completion_stream(
                    mock_guard,
                    {"messages": [{"role": "user", "content": "Test"}]},
                )
            )
            # Must consume generator inside patch context since it's lazy
            chunks = list(result)

        data_chunks = [c for c in chunks if c.startswith("data: ")]
        self.assertGreater(len(data_chunks), 0)

        first_chunk_data = json.loads(data_chunks[0][6:].strip())
        self.assertIn("guardrails", first_chunk_data)

    def test_stream_ends_with_final_newline(self):
        """Test that the stream ends with a final newline sentinel."""
        mock_chunk = self._make_mock_stream_chunk(content="End")
        mock_outcome = Mock()
        mock_outcome.model_dump.return_value = {"validation_passed": True}
        mock_outcome.validation_summaries = [Mock()]

        mock_guard = self._make_fake_stream_guard(mock_outcome)

        with patch(
            "guardrails_api.utils.openai.litellm.completion",
            side_effect=lambda *args, **kwargs: iter([mock_chunk]),
        ):
            result = asyncio.run(
                guarded_chat_completion_stream(
                    mock_guard,
                    {"messages": [{"role": "user", "content": "End"}]},
                )
            )
            # Must consume generator inside patch context since it's lazy
            chunks = list(result)

        self.assertEqual(chunks[-1], "\n")


if __name__ == "__main__":
    unittest.main()
