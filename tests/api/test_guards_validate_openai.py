"""Unit tests for validate and openai_v1_chat_completions endpoints."""
import unittest
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from guardrails import Guard
from guardrails.classes.history import Call, Iteration
from guardrails.errors import ValidationError
from guardrails_api.api.guards import router


class TestValidateEndpoint(unittest.TestCase):
    """Test cases for the /guards/{guard_name}/validate endpoint."""

    def setUp(self):
        """Set up test client and common mocks."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self.guard_name = "My Guard's Name"
        self.encoded_guard_name = "My%20Guard's%20Name"

    @patch.dict(os.environ, {"PGHOST": "localhost", "GUARD_HISTORY_ENABLED": "false"}, clear=False)
    @patch('guardrails_api.api.guards.get_guard_client')
    @patch('guardrails_api.api.guards.Guard.from_dict')
    def test_validate_parse(self, mock_from_dict, mock_get_guard_client):
        """Test validate endpoint with llmOutput (calls guard.parse)."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Create mock guard
        mock_guard = Mock(spec=Guard)
        mock_guard.name = self.guard_name

        # Mock the parse method to return a dict (as if to_dict() was called)
        mock_guard.parse.return_value = Mock()
        mock_guard.parse.return_value.to_dict.return_value = {
            "callId": "mock-call-id",
            "validatedOutput": "Hello world!",
            "validationPassed": True,
            "rawLlmOutput": "Hello world!",
        }

        # Setup mocks - return a guard struct that will be converted
        mock_guard_struct = Mock()
        mock_guard_struct.to_dict.return_value = {"name": self.guard_name}
        mock_from_dict.return_value = mock_guard
        mock_guard_client.get_guard.return_value = mock_guard_struct

        # Make request
        response = self.client.post(
            f"/guards/{self.encoded_guard_name}/validate",
            json={"llmOutput": "Hello world!", "args": [1, 2, 3], "some_kwarg": "foo"},
        )

        # Assertions
        mock_guard_client.get_guard.assert_called_once_with(self.guard_name)
        # Check that parse was called
        self.assertEqual(mock_guard.parse.call_count, 1)
        call_kwargs = mock_guard.parse.call_args[1]
        self.assertEqual(call_kwargs["llm_output"], "Hello world!")
        self.assertIsNone(call_kwargs["num_reasks"])
        self.assertEqual(call_kwargs["prompt_params"], {})
        self.assertIsNone(call_kwargs["llm_api"])
        self.assertEqual(call_kwargs["some_kwarg"], "foo")

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["callId"], "mock-call-id")
        self.assertEqual(response_data["validatedOutput"], "Hello world!")
        self.assertTrue(response_data["validationPassed"])
        self.assertEqual(response_data["rawLlmOutput"], "Hello world!")

    @patch.dict(os.environ, {"PGHOST": "localhost", "GUARD_HISTORY_ENABLED": "false"}, clear=False)
    @patch('guardrails_api.api.guards.get_guard_client')
    @patch('guardrails_api.api.guards.Guard.from_dict')
    def test_validate_call(self, mock_from_dict, mock_get_guard_client):
        """Test validate endpoint with prompt (calls guard.__call__)."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Create mock guard
        mock_guard = Mock()
        mock_guard.name = self.guard_name

        # Mock the return value for guard() call
        mock_result = Mock()
        mock_result.to_dict.return_value = {
            "callId": "mock-call-id",
            "validationPassed": False,
            "validatedOutput": None,
            "rawLlmOutput": "Hello world!",
        }
        mock_guard.return_value = mock_result

        # Setup mocks - return a guard struct that will be converted
        mock_guard_struct = Mock()
        mock_guard_struct.to_dict.return_value = {"name": self.guard_name}
        mock_from_dict.return_value = mock_guard
        mock_guard_client.get_guard.return_value = mock_guard_struct

        # Make request
        response = self.client.post(
            f"/guards/{self.encoded_guard_name}/validate",
            json={
                "promptParams": {"p1": "bar"},
                "args": [1, 2, 3],
                "some_kwarg": "foo",
                "prompt": "Hello world!",
            },
            headers={"x-openai-api-key": "mock-key"},
        )

        # Assertions
        mock_guard_client.get_guard.assert_called_once_with(self.guard_name)
        # Check call arguments
        self.assertEqual(mock_guard.call_count, 1)
        call_args = mock_guard.call_args
        self.assertEqual(call_args[0], (1, 2, 3))  # positional args
        self.assertIsNone(call_args[1]["llm_api"])
        self.assertEqual(call_args[1]["prompt_params"], {"p1": "bar"})
        self.assertIsNone(call_args[1]["num_reasks"])
        self.assertEqual(call_args[1]["some_kwarg"], "foo")
        self.assertEqual(call_args[1]["api_key"], "mock-key")
        self.assertEqual(call_args[1]["prompt"], "Hello world!")

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["callId"], "mock-call-id")
        self.assertFalse(response_data["validationPassed"])
        self.assertIsNone(response_data["validatedOutput"])
        self.assertEqual(response_data["rawLlmOutput"], "Hello world!")

    @patch.dict(os.environ, {"PGHOST": "localhost", "GUARD_HISTORY_ENABLED": "false"}, clear=False)
    @patch('guardrails_api.api.guards.get_guard_client')
    @patch('guardrails_api.api.guards.Guard.from_dict')
    def test_validate_call_throws_validation_error(
        self, mock_from_dict, mock_get_guard_client
    ):
        """Test validate endpoint when guard.__call__ raises ValidationError."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Create mock guard
        mock_guard = Mock()
        mock_guard.name = self.guard_name

        # Setup side_effect to raise ValidationError
        error = ValidationError("Test guard validation error")
        mock_guard.side_effect = error

        # Setup mocks - return a guard struct that will be converted
        mock_guard_struct = Mock()
        mock_guard_struct.to_dict.return_value = {"name": self.guard_name}
        mock_from_dict.return_value = mock_guard
        mock_guard_client.get_guard.return_value = mock_guard_struct

        # Make request
        response = self.client.post(
            f"/guards/{self.encoded_guard_name}/validate",
            json={
                "promptParams": {"p1": "bar"},
                "args": [1, 2, 3],
                "some_kwarg": "foo",
                "prompt": "Hello world!",
            },
        )

        # Assertions
        mock_guard_client.get_guard.assert_called_once_with(self.guard_name)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Test guard validation error")

    @patch.dict(os.environ, {"PGHOST": "localhost", "GUARD_HISTORY_ENABLED": "false"}, clear=False)
    @patch('guardrails_api.api.guards.get_guard_client')
    @patch('guardrails_api.api.guards.Guard.from_dict')
    def test_validate_parse_throws_validation_error(
        self, mock_from_dict, mock_get_guard_client
    ):
        """Test validate endpoint when guard.parse raises ValidationError."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Create mock guard
        mock_guard = Mock(spec=Guard)
        mock_guard.name = self.guard_name

        # Setup parse to raise ValidationError
        error = ValidationError("Test parse validation error")
        mock_guard.parse.side_effect = error

        # Setup mocks
        mock_guard_struct = Mock()
        mock_guard_struct.to_dict.return_value = {"name": self.guard_name}
        mock_from_dict.return_value = mock_guard
        mock_guard_client.get_guard.return_value = mock_guard_struct

        # Make request
        response = self.client.post(
            f"/guards/{self.encoded_guard_name}/validate",
            json={"llmOutput": "Hello world!"},
        )

        # Assertions
        mock_guard_client.get_guard.assert_called_once_with(self.guard_name)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Test parse validation error")

    @patch.dict(os.environ, {"PGHOST": "localhost", "OPENAI_API_KEY": "env-api-key", "GUARD_HISTORY_ENABLED": "false"}, clear=False)
    @patch('guardrails_api.api.guards.get_guard_client')
    @patch('guardrails_api.api.guards.Guard.from_dict')
    def test_validate_with_api_key_from_env(
        self, mock_from_dict, mock_get_guard_client
    ):
        """Test validate endpoint uses OPENAI_API_KEY from environment."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Create mock guard
        mock_guard = Mock(spec=Guard)
        mock_guard.name = self.guard_name

        mock_guard.parse.return_value = Mock()
        mock_guard.parse.return_value.to_dict.return_value = {
            "callId": "mock-call-id",
            "rawLlmOutput": "Hello!",
            "validatedOutput": "Hello!",
            "validationPassed": True,
        }

        # Setup mocks
        mock_guard_struct = Mock()
        mock_guard_struct.to_dict.return_value = {"name": self.guard_name}
        mock_from_dict.return_value = mock_guard
        mock_guard_client.get_guard.return_value = mock_guard_struct

        # Make request without x-openai-api-key header
        response = self.client.post(
            f"/guards/{self.encoded_guard_name}/validate",
            json={"llmOutput": "Hello!"},
        )

        # Should use env variable
        self.assertEqual(response.status_code, 200)
        call_args = mock_guard.parse.call_args
        self.assertEqual(call_args[1]["api_key"], "env-api-key")

    @patch.dict(os.environ, {"PGHOST": "localhost"}, clear=False)
    @patch('guardrails_api.api.guards.get_guard_client')
    @patch('guardrails_api.api.guards.Guard.from_dict')
    def test_validate_stream_with_parse_raises_error(
        self, mock_from_dict, mock_get_guard_client
    ):
        """Test validate endpoint raises error when stream=True with llmOutput."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Create mock guard
        mock_guard = Mock(spec=Guard)
        mock_guard.name = self.guard_name

        # Setup mocks
        mock_guard_struct = Mock()
        mock_guard_struct.to_dict.return_value = {"name": self.guard_name}
        mock_from_dict.return_value = mock_guard
        mock_guard_client.get_guard.return_value = mock_guard_struct

        # Make request with stream=True and llmOutput
        response = self.client.post(
            f"/guards/{self.encoded_guard_name}/validate",
            json={
                "llmOutput": "Hello world!",
                "stream": True,
            },
        )

        # Should raise 400 error
        self.assertEqual(response.status_code, 400)
        self.assertIn("Streaming is not supported for parse calls", response.json()["detail"])

    @patch('guardrails_api.api.guards.get_guard_client')
    @patch('guardrails_api.api.guards.get_llm_callable')
    def test_validate_with_llm_api_but_no_api_key(
        self, mock_get_llm_callable, mock_get_guard_client
    ):
        """Test validate endpoint raises error when llmApi is provided but no API key."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Setup mocks - return a guard struct with required fields
        mock_guard_struct = Mock()
        mock_guard_struct.to_dict.return_value = {
            "id": "test-guard-id",
            "name": self.guard_name,
            "railspec": "rail_spec: '1.0'\noutput_schema:\n  type: string",
        }
        mock_guard_client.get_guard.return_value = mock_guard_struct
        mock_get_llm_callable.return_value = Mock()

        # Temporarily remove OPENAI_API_KEY from environment if it exists
        old_api_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            # Make request with llmApi but no API key (and no x-openai-api-key header)
            response = self.client.post(
                f"/guards/{self.encoded_guard_name}/validate",
                json={
                    "llmApi": "openai.Completion.create",
                    "prompt": "Hello",
                },
            )

            # Should raise 400 error
            self.assertEqual(response.status_code, 400)
            self.assertIn("Cannot perform calls to OpenAI without an api key", response.json()["detail"])
        finally:
            # Restore old API key if it existed
            if old_api_key is not None:
                os.environ["OPENAI_API_KEY"] = old_api_key

    @patch.dict(os.environ, {"PGHOST": "localhost"}, clear=False)
    @patch('guardrails_api.api.guards.get_guard_client')
    @patch('guardrails_api.api.guards.Guard.from_dict')
    def test_validate_reasks_without_llm_api(
        self, mock_from_dict, mock_get_guard_client
    ):
        """Test validate endpoint raises error when num_reasks > 1 without llm_api."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Create mock guard
        mock_guard = Mock(spec=Guard)
        mock_guard.name = self.guard_name

        # Setup mocks
        mock_guard_struct = Mock()
        mock_guard_struct.to_dict.return_value = {"name": self.guard_name}
        mock_from_dict.return_value = mock_guard
        mock_guard_client.get_guard.return_value = mock_guard_struct

        # Make request with numReasks > 1 but no llmApi
        response = self.client.post(
            f"/guards/{self.encoded_guard_name}/validate",
            json={
                "numReasks": 2,
                "prompt": "Hello",
            },
        )

        # Should raise 400 error
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot perform re-asks without an LLM API", response.json()["detail"])


class TestOpenAIV1ChatCompletionsEndpoint(unittest.TestCase):
    """Test cases for the /guards/{guard_name}/openai/v1/chat/completions endpoint."""

    def setUp(self):
        """Set up test client and common mocks."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self.guard_name = "My Guard's Name"
        self.encoded_guard_name = "My%20Guard's%20Name"

    @patch.dict(os.environ, {"PGHOST": "localhost"}, clear=False)
    @patch('guardrails_api.api.guards.get_guard_client')
    def test_openai_v1_chat_completions_raises_404(self, mock_get_guard_client):
        """Test OpenAI chat completions endpoint returns 404 when guard not found."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Setup guard_client to return None
        mock_guard_client.get_guard.return_value = None

        # Make request
        response = self.client.post(
            f"/guards/{self.encoded_guard_name}/openai/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello world!"}],
            },
            headers={"x-openai-api-key": "mock-key"},
        )

        # Assertions
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            f"A Guard with the name {self.guard_name} does not exist!"
        )
        mock_guard_client.get_guard.assert_called_once_with(self.guard_name)

    @patch.dict(os.environ, {"PGHOST": "localhost"}, clear=False)
    @patch('guardrails_api.api.guards.get_guard_client')
    @patch('guardrails_api.api.guards.AsyncGuard.from_dict')
    @patch('guardrails_api.api.guards.outcome_to_chat_completion')
    @patch('guardrails_api.api.guards.inspect.iscoroutine')
    def test_openai_v1_chat_completions_call(
        self, mock_iscoroutine, mock_outcome_to_chat, mock_async_from_dict, mock_get_guard_client
    ):
        """Test OpenAI chat completions endpoint successful call."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Create mock guard
        mock_guard = Mock()
        mock_guard.name = self.guard_name

        # Create mock validation outcome
        mock_outcome = Mock()

        # Setup return_value for guard() call
        mock_guard.return_value = mock_outcome

        # Setup history with iterations
        mock_outputs = Mock()
        mock_outputs.llm_response_info = {"model": "gpt-4"}

        mock_iteration = Mock(spec=Iteration)
        mock_iteration.outputs = mock_outputs

        mock_iterations = Mock()
        mock_iterations.last = mock_iteration

        mock_call = Mock(spec=Call)
        mock_call.iterations = mock_iterations

        mock_history = Mock()
        mock_history.last = mock_call
        mock_guard.history = mock_history

        # Setup the outcome_to_chat_completion mock
        expected_response = {
            "choices": [
                {
                    "message": {
                        "content": "Hello world!",
                    },
                }
            ],
            "guardrails": {
                "reask": None,
                "validation_passed": False,
                "error": None,
            },
        }
        mock_outcome_to_chat.return_value = expected_response

        # Setup mocks - return a guard struct (not a Guard instance)
        mock_guard_struct = Mock()
        mock_guard_struct.to_dict.return_value = {"name": self.guard_name}
        mock_async_from_dict.return_value = mock_guard
        mock_guard_client.get_guard.return_value = mock_guard_struct
        mock_iscoroutine.return_value = False

        # Make request
        response = self.client.post(
            f"/guards/{self.encoded_guard_name}/openai/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello world!"}],
            },
            headers={"x-openai-api-key": "mock-key"},
        )

        # Assertions
        mock_guard_client.get_guard.assert_called_once_with(self.guard_name)
        mock_guard.assert_called_once_with(
            num_reasks=0,
            messages=[{"role": "user", "content": "Hello world!"}],
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("choices", response_data)
        self.assertIn("guardrails", response_data)
        self.assertEqual(response_data["choices"][0]["message"]["content"], "Hello world!")
        self.assertFalse(response_data["guardrails"]["validation_passed"])

    @patch.dict(os.environ, {"PGHOST": "localhost"}, clear=False)
    @patch('guardrails_api.api.guards.get_guard_client')
    @patch('guardrails_api.api.guards.AsyncGuard.from_dict')
    @patch('guardrails_api.api.guards.outcome_to_chat_completion')
    @patch('guardrails_api.api.guards.inspect.iscoroutine')
    def test_openai_v1_chat_completions_with_tools(
        self, mock_iscoroutine, mock_outcome_to_chat, mock_async_from_dict, mock_get_guard_client
    ):
        """Test OpenAI chat completions with gd_response_tool."""
        # Setup mock guard client first
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        # Create mock guard
        mock_guard = Mock()
        mock_guard.name = self.guard_name

        # Create mock validation outcome
        mock_outcome = Mock()

        # Setup return_value for guard() call
        mock_guard.return_value = mock_outcome

        # Setup history
        mock_outputs = Mock()
        mock_outputs.llm_response_info = {"model": "gpt-4"}

        mock_iteration = Mock(spec=Iteration)
        mock_iteration.outputs = mock_outputs

        mock_iterations = Mock()
        mock_iterations.last = mock_iteration

        mock_call = Mock(spec=Call)
        mock_call.iterations = mock_iterations

        mock_history = Mock()
        mock_history.last = mock_call
        mock_guard.history = mock_history

        # Setup outcome_to_chat_completion
        expected_response = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "gd_response_tool",
                                    "arguments": '{"validated_output": "Tool response!"}'
                                }
                            }
                        ]
                    },
                }
            ],
            "guardrails": {
                "reask": None,
                "validation_passed": True,
                "error": None,
            },
        }
        mock_outcome_to_chat.return_value = expected_response

        # Setup mocks
        mock_guard_struct = Mock()
        mock_guard_struct.to_dict.return_value = {"name": self.guard_name}
        mock_async_from_dict.return_value = mock_guard
        mock_guard_client.get_guard.return_value = mock_guard_struct
        mock_iscoroutine.return_value = False

        # Make request with gd_response_tool
        response = self.client.post(
            f"/guards/{self.encoded_guard_name}/openai/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello!"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "gd_response_tool",
                            "description": "Guardrails response tool"
                        }
                    }
                ]
            },
        )

        # Assertions
        self.assertEqual(response.status_code, 200)

        # Verify outcome_to_chat_completion was called with has_tool_gd_tool_call=True
        call_args = mock_outcome_to_chat.call_args
        self.assertTrue(call_args[1]["has_tool_gd_tool_call"])


if __name__ == "__main__":
    unittest.main()
