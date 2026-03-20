"""Unit tests for validate and openai_v1_chat_completions endpoints."""

import unittest
import os
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from guardrails import AsyncGuard
from guardrails.errors import ValidationError
from guardrails_ai.types import Guard as IGuard
from guardrails_api.api.guards import router

HISTORY_OFF = {"GUARD_HISTORY_ENABLED": "false"}
PGHOST = {"PGHOST": "localhost"}
BASE_ENV = {**PGHOST, **HISTORY_OFF}

# A minimal serializable outcome dict that FastAPI can return directly.
_OUTCOME = {
    "callId": "mock-call-id",
    "validationPassed": True,
    "validatedOutput": "Hello!",
    "rawLlmOutput": "Hello!",
}


def _guard_client(guard_struct):
    gc = Mock()
    gc.get_guard.return_value = guard_struct
    return gc


class TestValidateEndpoint(unittest.TestCase):
    """Tests for POST /guards/{id}/validate."""

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self._id = "my-guard"
        # Real IGuard so isinstance(guard_struct, IGuard) is True in the endpoint,
        # which triggers the AsyncGuard.from_dict path.
        self.guard_struct = IGuard(name="my-guard", id=self._id)

    # ------------------------------------------------------------------ #
    # parse path (llm_output present)
    # ------------------------------------------------------------------ #

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.attach_validation_summaries")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_llm_output_routes_to_parse(self, mock_from_dict, mock_get_gc, mock_attach):
        """When llm_output is provided, guard.parse is called (not guard.__call__)."""
        mock_guard = Mock(spec=AsyncGuard)
        mock_guard.parse = AsyncMock(return_value=Mock())
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        mock_attach.return_value = _OUTCOME

        response = self.client.post(
            f"/guards/{self._id}/validate",
            json={"llm_output": "Hello!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_guard.parse.call_count, 1)

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.attach_validation_summaries")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_parse_receives_correct_kwargs(
        self, mock_from_dict, mock_get_gc, mock_attach
    ):
        """guard.parse is called with llm_output, prompt_params, num_reasks, and api_key."""
        mock_guard = Mock(spec=AsyncGuard)
        mock_guard.parse = AsyncMock(return_value=Mock())
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        mock_attach.return_value = _OUTCOME

        self.client.post(
            f"/guards/{self._id}/validate",
            json={"llm_output": "Hello!", "prompt_params": {"k": "v"}, "num_reasks": 2},
            headers={"x-openai-api-key": "test-key"},
        )

        kwargs = mock_guard.parse.call_args.kwargs
        self.assertEqual(kwargs["llm_output"], "Hello!")
        self.assertEqual(kwargs["prompt_params"], {"k": "v"})
        self.assertEqual(kwargs["num_reasks"], 2)
        self.assertEqual(kwargs["api_key"], "test-key")
        # llm_api is stripped from the payload before calling parse
        self.assertNotIn("llm_api", kwargs)

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.attach_validation_summaries")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_parse_result_returned_in_response(
        self, mock_from_dict, mock_get_gc, mock_attach
    ):
        """Response body reflects the outcome returned by attach_validation_summaries."""
        mock_guard = Mock(spec=AsyncGuard)
        mock_guard.parse = AsyncMock(return_value=Mock())
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        mock_attach.return_value = _OUTCOME

        response = self.client.post(
            f"/guards/{self._id}/validate",
            json={"llm_output": "Hello!"},
        )

        data = response.json()
        self.assertEqual(data["callId"], "mock-call-id")
        self.assertTrue(data["validationPassed"])
        self.assertEqual(data["validatedOutput"], "Hello!")

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_parse_validation_error_returns_400(self, mock_from_dict, mock_get_gc):
        """ValidationError raised by guard.parse yields a 400 response."""
        mock_guard = Mock(spec=AsyncGuard)
        mock_guard.parse = AsyncMock(side_effect=ValidationError("bad output"))
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)

        response = self.client.post(
            f"/guards/{self._id}/validate",
            json={"llm_output": "Hello!"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("bad output", response.json()["detail"])

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_stream_with_llm_output_returns_400(self, mock_from_dict, mock_get_gc):
        """stream=True combined with llm_output is not supported and returns 400."""
        mock_guard = Mock(spec=AsyncGuard)
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)

        response = self.client.post(
            f"/guards/{self._id}/validate",
            json={"llm_output": "Hello!", "stream": True},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Streaming is not supported", response.json()["detail"])

    # ------------------------------------------------------------------ #
    # guard.__call__ path (no llm_output)
    # ------------------------------------------------------------------ #

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.attach_validation_summaries")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_no_llm_output_calls_guard(self, mock_from_dict, mock_get_gc, mock_attach):
        """Without llm_output, guard.__call__ is invoked instead of guard.parse."""
        mock_guard = Mock()
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        mock_attach.return_value = _OUTCOME

        response = self.client.post(
            f"/guards/{self._id}/validate",
            json={},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_guard.call_count, 1)

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.attach_validation_summaries")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_call_receives_correct_kwargs(
        self, mock_from_dict, mock_get_gc, mock_attach
    ):
        """guard() receives prompt_params, num_reasks, and api_key."""
        mock_guard = Mock()
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        mock_attach.return_value = _OUTCOME

        self.client.post(
            f"/guards/{self._id}/validate",
            json={"prompt_params": {"p": "val"}, "num_reasks": 1},
            headers={"x-openai-api-key": "header-key"},
        )

        kwargs = mock_guard.call_args.kwargs
        self.assertEqual(kwargs["prompt_params"], {"p": "val"})
        self.assertEqual(kwargs["num_reasks"], 1)
        self.assertEqual(kwargs["api_key"], "header-key")

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_call_validation_error_returns_400(self, mock_from_dict, mock_get_gc):
        """ValidationError raised by guard.__call__ yields a 400 response."""
        mock_guard = Mock()
        mock_guard.side_effect = ValidationError("invalid")
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)

        response = self.client.post(
            f"/guards/{self._id}/validate",
            json={},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid", response.json()["detail"])

    # ------------------------------------------------------------------ #
    # API key resolution
    # ------------------------------------------------------------------ #

    @patch.dict(os.environ, {**BASE_ENV, "OPENAI_API_KEY": "env-key"})
    @patch("guardrails_api.api.guards.attach_validation_summaries")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_api_key_falls_back_to_env_var(
        self, mock_from_dict, mock_get_gc, mock_attach
    ):
        """OPENAI_API_KEY env var is used when no x-openai-api-key header is sent."""
        mock_guard = Mock(spec=AsyncGuard)
        mock_guard.parse = AsyncMock(return_value=Mock())
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        mock_attach.return_value = _OUTCOME

        self.client.post(
            f"/guards/{self._id}/validate",
            json={"llm_output": "Hello!"},
        )

        self.assertEqual(mock_guard.parse.call_args.kwargs["api_key"], "env-key")

    @patch.dict(os.environ, {**BASE_ENV, "OPENAI_API_KEY": "env-key"})
    @patch("guardrails_api.api.guards.attach_validation_summaries")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_header_api_key_overrides_env_var(
        self, mock_from_dict, mock_get_gc, mock_attach
    ):
        """x-openai-api-key header takes precedence over OPENAI_API_KEY env var."""
        mock_guard = Mock(spec=AsyncGuard)
        mock_guard.parse = AsyncMock(return_value=Mock())
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        mock_attach.return_value = _OUTCOME

        self.client.post(
            f"/guards/{self._id}/validate",
            json={"llm_output": "Hello!"},
            headers={"x-openai-api-key": "header-key"},
        )

        self.assertEqual(mock_guard.parse.call_args.kwargs["api_key"], "header-key")

    # ------------------------------------------------------------------ #
    # Guard lookup
    # ------------------------------------------------------------------ #

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_guard_not_found_returns_404(self, mock_get_gc):
        """Returns 404 when the guard does not exist."""
        mock_get_gc.return_value = _guard_client(None)

        response = self.client.post(
            f"/guards/{self._id}/validate",
            json={},
        )

        self.assertEqual(response.status_code, 404)

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.attach_validation_summaries")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_guard_fetched_by_decoded_id(
        self, mock_from_dict, mock_get_gc, mock_attach
    ):
        """get_guard is called with the URL-decoded guard id."""
        mock_guard = Mock()
        mock_from_dict.return_value = mock_guard
        mock_gc = Mock()
        mock_gc.get_guard.return_value = self.guard_struct
        mock_get_gc.return_value = mock_gc
        mock_attach.return_value = _OUTCOME

        self.client.post(f"/guards/{self._id}/validate", json={})

        mock_gc.get_guard.assert_called_once_with(self._id)

    @patch.dict(os.environ, BASE_ENV)
    @patch("guardrails_api.api.guards.attach_validation_summaries")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_from_dict_called_with_guard_struct_data(
        self, mock_from_dict, mock_get_gc, mock_attach
    ):
        """AsyncGuard.from_dict receives the model_dump of the IGuard struct."""
        mock_guard = Mock()
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        mock_attach.return_value = _OUTCOME

        self.client.post(f"/guards/{self._id}/validate", json={})

        mock_from_dict.assert_called_once_with(
            self.guard_struct.model_dump(exclude_none=True)
        )


class TestOpenAIV1ChatCompletionsEndpoint(unittest.TestCase):
    """Tests for POST /guards/{id}/openai/v1/chat/completions."""

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self._id = "my-guard"
        self.guard_struct = IGuard(name="my-guard", id=self._id)

    _CHAT_PAYLOAD = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello!"}],
    }

    @patch.dict(os.environ, PGHOST)
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_guard_not_found_returns_404(self, mock_get_gc):
        """Returns 404 when the guard does not exist."""
        mock_get_gc.return_value = _guard_client(None)

        response = self.client.post(
            f"/guards/{self._id}/openai/v1/chat/completions",
            json=self._CHAT_PAYLOAD,
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("does not exist", response.json()["detail"])

    @patch.dict(os.environ, PGHOST)
    @patch("guardrails_api.api.guards.guarded_chat_completion")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_successful_call_returns_200(
        self, mock_from_dict, mock_get_gc, mock_completion
    ):
        """A valid request returns 200 with choices and guardrails fields."""
        mock_guard = Mock()
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        mock_completion.return_value = {
            "choices": [{"message": {"content": "Hello!"}}],
            "guardrails": {"reask": None, "validation_passed": True, "error": None},
        }

        response = self.client.post(
            f"/guards/{self._id}/openai/v1/chat/completions",
            json=self._CHAT_PAYLOAD,
            headers={"x-openai-api-key": "mock-key"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("choices", data)
        self.assertIn("guardrails", data)
        self.assertEqual(data["choices"][0]["message"]["content"], "Hello!")

    @patch.dict(os.environ, PGHOST)
    @patch("guardrails_api.api.guards.guarded_chat_completion")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_passes_guard_and_payload_to_guarded_chat_completion(
        self, mock_from_dict, mock_get_gc, mock_completion
    ):
        """guarded_chat_completion receives the resolved guard and the full payload."""
        mock_guard = Mock()
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        mock_completion.return_value = {"choices": [], "guardrails": {}}

        self.client.post(
            f"/guards/{self._id}/openai/v1/chat/completions",
            json=self._CHAT_PAYLOAD,
        )

        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[0]
        self.assertIs(call_args[0], mock_guard)
        self.assertEqual(call_args[1]["model"], "gpt-4")
        self.assertIn("messages", call_args[1])

    @patch.dict(os.environ, PGHOST)
    @patch("guardrails_api.api.guards.guarded_chat_completion")
    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.AsyncGuard.from_dict")
    def test_tools_forwarded_in_payload(
        self, mock_from_dict, mock_get_gc, mock_completion
    ):
        """Tools array is forwarded to guarded_chat_completion in the payload."""
        mock_guard = Mock()
        mock_from_dict.return_value = mock_guard
        mock_get_gc.return_value = _guard_client(self.guard_struct)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "gd_response_tool",
                    "description": "Guardrails tool",
                },
            }
        ]
        mock_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "gd_response_tool",
                                    "arguments": '{"validated_output": "ok"}',
                                }
                            }
                        ],
                    }
                }
            ],
            "guardrails": {"reask": None, "validation_passed": True, "error": None},
        }

        response = self.client.post(
            f"/guards/{self._id}/openai/v1/chat/completions",
            json={**self._CHAT_PAYLOAD, "tools": tools},
        )

        self.assertEqual(response.status_code, 200)
        payload_arg = mock_completion.call_args[0][1]
        self.assertIn("tools", payload_arg)
        self.assertEqual(payload_arg["tools"], tools)

    @patch.dict(os.environ, PGHOST)
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_guard_fetched_by_decoded_id(self, mock_get_gc):
        """get_guard is called with the URL-decoded guard id."""
        mock_gc = Mock()
        mock_gc.get_guard.return_value = (
            None  # causes 404, but we only care about the call
        )
        mock_get_gc.return_value = mock_gc

        self.client.post(
            f"/guards/{self._id}/openai/v1/chat/completions",
            json=self._CHAT_PAYLOAD,
        )

        mock_gc.get_guard.assert_called_once_with(self._id)


if __name__ == "__main__":
    unittest.main()
