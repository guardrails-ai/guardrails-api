"""Unit tests for guardrails_api.api.guards module."""

import json
import unittest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from guardrails_api.api.guards import router, guard_history_is_enabled, get_guard_body
from guardrails_api.classes.http_error import HttpError
from guardrails_api.clients.memory_guard_client import MemoryGuardClient


class TestGuardHistoryIsEnabled(unittest.TestCase):
    """Test cases for guard_history_is_enabled function."""

    @patch.dict("os.environ", {}, clear=True)
    def test_guard_history_enabled_by_default(self):
        """Test that guard history is enabled by default."""
        result = guard_history_is_enabled()
        self.assertTrue(result)

    @patch.dict("os.environ", {"GUARD_HISTORY_ENABLED": "true"})
    def test_guard_history_enabled_when_true(self):
        """Test guard history when explicitly set to true."""
        result = guard_history_is_enabled()
        self.assertTrue(result)

    @patch.dict("os.environ", {"GUARD_HISTORY_ENABLED": "True"})
    def test_guard_history_enabled_case_insensitive(self):
        """Test guard history setting is case insensitive."""
        result = guard_history_is_enabled()
        self.assertTrue(result)

    @patch.dict("os.environ", {"GUARD_HISTORY_ENABLED": "false"})
    def test_guard_history_disabled_when_false(self):
        """Test guard history when set to false."""
        result = guard_history_is_enabled()
        self.assertFalse(result)

    @patch.dict("os.environ", {"GUARD_HISTORY_ENABLED": "FALSE"})
    def test_guard_history_disabled_case_insensitive(self):
        """Test guard history disabled is case insensitive."""
        result = guard_history_is_enabled()
        self.assertFalse(result)

    @patch.dict("os.environ", {"GUARD_HISTORY_ENABLED": "invalid"})
    def test_guard_history_disabled_with_invalid_value(self):
        """Test guard history with invalid value."""
        result = guard_history_is_enabled()
        self.assertFalse(result)


class TestGuardsAPI(unittest.TestCase):
    """Test cases for the guards API endpoints."""

    def setUp(self):
        """Set up test client and mocks."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guards(self, mock_get_guard_client, mock_postgres_is_enabled):
        """Test GET /guards endpoint."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard1 = Mock()
        mock_guard1.to_dict.return_value = {"name": "guard1", "description": "Test 1"}
        mock_guard2 = Mock()
        mock_guard2.to_dict.return_value = {"name": "guard2", "description": "Test 2"}

        mock_guard_client.get_guards.return_value = [mock_guard1, mock_guard2]

        response = self.client.get("/guards")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "guard1")
        self.assertEqual(data[1]["name"], "guard2")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guards_empty_list(
        self, mock_get_guard_client, mock_postgres_is_enabled
    ):
        """Test GET /guards when no guards exist."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard_client.get_guards.return_value = []

        response = self.client.get("/guards")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_create_guard_not_implemented_for_memory(
        self, mock_get_guard_client, mock_postgres
    ):
        """Test POST /guards fails for in-memory guards."""
        mock_postgres.return_value = False
        mock_get_guard_client.return_value = MemoryGuardClient()

        response = self.client.post(
            "/guards", json={"name": "test_guard", "description": "Test"}
        )

        self.assertEqual(response.status_code, 501)
        self.assertIn("Not Implemented", response.json()["detail"])

    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.GuardStruct")
    def test_create_guard_success(
        self, mock_guard_struct_class, mock_postgres, mock_get_guard_client
    ):
        """Test POST /guards successfully creates a guard."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_postgres.return_value = True

        mock_guard = Mock()
        mock_guard.to_dict.return_value = {"name": "test_guard", "description": "Test"}
        mock_guard_struct_class.from_json.return_value = mock_guard

        mock_new_guard = Mock()
        mock_new_guard.to_dict.return_value = {"name": "test_guard", "id": "123"}
        mock_guard_client.create_guard.return_value = mock_new_guard

        response = self.client.post(
            "/guards", json={"name": "test_guard", "description": "Test"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "test_guard")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_success(self, mock_get_guard_client, mock_postgres_is_enabled):
        """Test GET /guards/{id} successfully retrieves a guard."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard = Mock()
        mock_guard.to_dict.return_value = {
            "id": "test-guard",
            "name": "test_guard",
            "description": "Test",
        }
        mock_guard_client.get_guard.return_value = mock_guard

        response = self.client.get("/guards/test-guard")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "test_guard")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_not_found(self, mock_get_guard_client, mock_postgres_is_enabled):
        """Test GET /guards/{id} returns 404 when guard not found."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard_client.get_guard.return_value = None

        response = self.client.get("/guards/nonexistent")

        self.assertEqual(response.status_code, 404)
        self.assertIn("does not exist", response.json()["detail"])

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_url_encoded_name(
        self, mock_get_guard_client, mock_postgres_is_enabled
    ):
        """Test GET /guards/{id} handles URL-encoded names."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard = Mock()
        mock_guard.to_dict.return_value = {
            "id": "test guard",
            "name": "test guard",
            "description": "Test",
        }
        mock_guard_client.get_guard.return_value = mock_guard

        # "test guard" URL encoded is "test+guard"
        response = self.client.get("/guards/test+guard")

        self.assertEqual(response.status_code, 200)
        # Verify the decoded name was passed to get_guard
        mock_guard_client.get_guard.assert_called_once_with("test guard", None)

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_with_as_of_date(
        self, mock_get_guard_client, mock_postgres_is_enabled
    ):
        """Test GET /guards/{id} with asOf parameter."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard = Mock()
        mock_guard.to_dict.return_value = {"id": "test-guard", "name": "test_guard"}
        mock_guard_client.get_guard.return_value = mock_guard

        response = self.client.get("/guards/test-guard?asOf=2024-01-01")

        self.assertEqual(response.status_code, 200)
        mock_guard_client.get_guard.assert_called_once_with("test-guard", "2024-01-01")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_update_guard_not_implemented_for_memory(
        self, mock_get_guard_client, mock_postgres_is_enabled
    ):
        """Test PUT /guards/{id} fails for in-memory guards."""
        mock_postgres_is_enabled.return_value = False
        mock_get_guard_client.return_value = MemoryGuardClient()

        response = self.client.put(
            "/guards/test-guard",
            json={"id": "test-guard", "name": "test_guard", "description": "Updated"},
        )

        self.assertEqual(response.status_code, 501)
        self.assertIn("not implemented", response.json()["detail"])

    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.GuardStruct")
    def test_update_guard_success(
        self, mock_guard_struct_class, mock_postgres, mock_get_guard_client
    ):
        """Test PUT /guards/{id} successfully updates a guard."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_postgres.return_value = True

        mock_guard = Mock()
        mock_guard_struct_class.from_json.return_value = mock_guard

        mock_updated_guard = Mock()
        mock_updated_guard.to_dict.return_value = {
            "name": "test_guard",
            "description": "Updated",
        }
        mock_guard_client.upsert_guard.return_value = mock_updated_guard

        response = self.client.put(
            "/guards/test-guard",
            json={"id": "test-guard", "name": "test_guard", "description": "Updated"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["description"], "Updated")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_delete_guard_not_implemented_for_memory(
        self, mock_get_guard_client, mock_postgres
    ):
        """Test DELETE /guards/{id} fails for in-memory guards."""
        mock_postgres.return_value = False
        mock_get_guard_client.return_value = MemoryGuardClient()

        response = self.client.delete("/guards/test_guard")

        self.assertEqual(response.status_code, 501)
        self.assertIn("not implemented", response.json()["detail"])

    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.postgres_is_enabled")
    def test_delete_guard_success(self, mock_postgres, mock_get_guard_client):
        """Test DELETE /guards/{id} successfully deletes a guard."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_postgres.return_value = True

        mock_guard = Mock()
        mock_guard.to_dict.return_value = {"name": "test_guard"}
        mock_guard_client.delete_guard.return_value = mock_guard

        response = self.client.delete("/guards/test_guard")

        self.assertEqual(response.status_code, 200)
        mock_guard_client.delete_guard.assert_called_once_with("test_guard")

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_openai_chat_completions_guard_not_found(self, mock_get_guard_client):
        """Test OpenAI chat completions endpoint when guard not found."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard_client.get_guard.return_value = None

        response = self.client.post(
            "/guards/nonexistent/openai/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )

        self.assertEqual(response.status_code, 404)

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_validate_endpoint_exists(self, mock_get_guard_client):
        """Test that validate endpoint exists and is accessible."""
        # Just verify the endpoint is registered
        routes = [route.path for route in self.app.routes]
        self.assertIn("/guards/{id}/validate", routes)

    @patch("guardrails_api.api.guards.cache_client")
    def test_guard_history_endpoint(self, mock_cache_client):
        """Test GET /guards/{id}/history/{call_id} endpoint."""
        mock_history = [{"iteration": 1, "result": "passed"}]
        mock_cache_client.get = AsyncMock(return_value=mock_history)

        response = self.client.get("/guards/test_guard/history/call-123")

        self.assertEqual(response.status_code, 200)

    def test_router_exists(self):
        """Test that router is properly created."""
        from fastapi import APIRouter

        self.assertIsInstance(router, APIRouter)

    def test_all_endpoints_registered(self):
        """Test that all expected endpoints are registered."""
        routes = [route.path for route in self.app.routes]

        expected_routes = [
            "/guards",
            "/guards/{id}",
            "/guards/{id}/openai/v1/chat/completions",
            "/guards/{id}/validate",
            "/guards/{id}/history/{call_id}",
        ]

        for expected_route in expected_routes:
            self.assertIn(expected_route, routes)

    def test_get_guards_endpoint_methods(self):
        """Test GET /guards endpoint exists."""
        methods = []
        for route in self.app.routes:
            if route.path == "/guards" and hasattr(route, "methods"):
                methods.extend(route.methods)
        self.assertIn("GET", methods)

    def test_create_guard_endpoint_methods(self):
        """Test POST /guards endpoint exists."""
        methods = []
        for route in self.app.routes:
            if route.path == "/guards" and hasattr(route, "methods"):
                methods.extend(route.methods)
        self.assertIn("POST", methods)

    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.GuardStruct")
    def test_create_guard_invalid_payload(
        self, mock_guard_struct, mock_postgres, mock_get_guard_client
    ):
        """Test POST /guards with invalid payload returns 422."""
        mock_get_guard_client.return_value = Mock()
        mock_postgres.return_value = True
        mock_guard_struct.from_json.return_value = None

        response = self.client.post("/guards", json={})

        self.assertEqual(response.status_code, 422)

    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.GuardStruct")
    def test_update_guard_invalid_payload(
        self, mock_guard_struct, mock_postgres, mock_get_guard_client
    ):
        """Test PUT /guards/{id} with invalid payload returns 422."""
        mock_get_guard_client.return_value = Mock()
        mock_postgres.return_value = True
        mock_guard_struct.from_json.return_value = None

        response = self.client.put("/guards/test_guard", json={})

        self.assertEqual(response.status_code, 422)


class TestGetGuardBody(unittest.IsolatedAsyncioTestCase):
    """Test cases for the get_guard_body async function."""

    def _make_request(self, method: str, body_dict: dict) -> AsyncMock:
        mock_request = AsyncMock()
        mock_request.method = method
        mock_request.body.return_value = json.dumps(body_dict).encode("utf-8")
        return mock_request

    @patch("guardrails_api.api.guards.GuardStruct")
    async def test_returns_guard_struct_from_from_json(self, mock_guard_struct):
        """Test that the parsed GuardStruct is returned on success."""
        mock_guard = Mock()
        mock_guard_struct.from_json.return_value = mock_guard

        result = await get_guard_body(self._make_request("GET", {"name": "test"}))

        self.assertEqual(result, mock_guard)

    @patch("guardrails_api.api.guards.GuardStruct")
    async def test_post_without_id_injects_uuid(self, mock_guard_struct):
        """Test that POST requests without an id get a UUID assigned."""
        mock_guard_struct.from_json.return_value = Mock()

        with patch("guardrails_api.api.guards.uuid") as mock_uuid:
            mock_uuid.uuid4.return_value = "generated-uuid"
            await get_guard_body(self._make_request("POST", {"name": "test"}))

        mock_uuid.uuid4.assert_called_once()
        call_json = mock_guard_struct.from_json.call_args[0][0]
        self.assertEqual(json.loads(call_json)["id"], "generated-uuid")

    @patch("guardrails_api.api.guards.GuardStruct")
    async def test_post_with_null_id_injects_uuid(self, mock_guard_struct):
        """Test that POST with id=null (falsy) generates a UUID."""
        mock_guard_struct.from_json.return_value = Mock()

        with patch("guardrails_api.api.guards.uuid") as mock_uuid:
            mock_uuid.uuid4.return_value = "generated-uuid"
            await get_guard_body(
                self._make_request("POST", {"name": "test", "id": None})
            )

        mock_uuid.uuid4.assert_called_once()

    @patch("guardrails_api.api.guards.GuardStruct")
    async def test_post_with_existing_id_preserves_it(self, mock_guard_struct):
        """Test that POST requests with an existing id do not overwrite it."""
        mock_guard_struct.from_json.return_value = Mock()

        with patch("guardrails_api.api.guards.uuid") as mock_uuid:
            await get_guard_body(
                self._make_request("POST", {"name": "test", "id": "my-id"})
            )

        mock_uuid.uuid4.assert_not_called()
        call_json = mock_guard_struct.from_json.call_args[0][0]
        self.assertEqual(json.loads(call_json)["id"], "my-id")

    @patch("guardrails_api.api.guards.GuardStruct")
    async def test_put_does_not_inject_id(self, mock_guard_struct):
        """Test that non-POST methods do not inject a UUID."""
        mock_guard_struct.from_json.return_value = Mock()

        with patch("guardrails_api.api.guards.uuid") as mock_uuid:
            await get_guard_body(self._make_request("PUT", {"name": "test"}))

        mock_uuid.uuid4.assert_not_called()

    @patch("guardrails_api.api.guards.GuardStruct")
    async def test_get_does_not_inject_id(self, mock_guard_struct):
        """Test that GET method does not inject a UUID."""
        mock_guard_struct.from_json.return_value = Mock()

        with patch("guardrails_api.api.guards.uuid") as mock_uuid:
            await get_guard_body(self._make_request("GET", {"name": "test"}))

        mock_uuid.uuid4.assert_not_called()

    @patch("guardrails_api.api.guards.GuardStruct")
    async def test_passes_full_body_to_from_json(self, mock_guard_struct):
        """Test that the full body dict is serialized and passed to GuardStruct.from_json."""
        mock_guard_struct.from_json.return_value = Mock()
        body = {"name": "my_guard", "description": "A guard"}

        await get_guard_body(self._make_request("GET", body))

        call_json = mock_guard_struct.from_json.call_args[0][0]
        parsed = json.loads(call_json)
        self.assertEqual(parsed["name"], "my_guard")
        self.assertEqual(parsed["description"], "A guard")

    @patch("guardrails_api.api.guards.GuardStruct")
    async def test_validation_error_raises_http_400(self, mock_guard_struct):
        """Test that a ValidationError from from_json raises HttpError 400."""
        from pydantic import BaseModel, ValidationError

        class _M(BaseModel):
            x: int

        try:
            _M(x="bad")  # type: ignore[arg-type]
        except ValidationError as ve:
            mock_guard_struct.from_json.side_effect = ve

        with self.assertRaises(HttpError) as ctx:
            await get_guard_body(self._make_request("GET", {"name": "test"}))

        error = ctx.exception
        self.assertEqual(error.status, 400)
        self.assertEqual(error.message, "BadRequest")
        self.assertIsNotNone(error.fields)

    @patch("guardrails_api.api.guards.GuardStruct")
    async def test_validation_error_maps_field_loc_to_path(self, mock_guard_struct):
        """Test that ValidationError field loc is joined into a dot-separated path."""
        from pydantic import BaseModel, ValidationError

        class _M(BaseModel):
            my_field: int

        try:
            _M(my_field="bad")  # type: ignore[arg-type]
        except ValidationError as ve:
            mock_guard_struct.from_json.side_effect = ve

        with self.assertRaises(HttpError) as ctx:
            await get_guard_body(self._make_request("GET", {"name": "test"}))

        error = ctx.exception
        self.assertIsNotNone(error.fields)
        self.assertIn("my_field", error.fields)  # type: ignore[arg-type]

    @patch("guardrails_api.api.guards.GuardStruct")
    async def test_validation_error_nested_loc_joined_by_dot(self, mock_guard_struct):
        """Test that nested ValidationError locs are joined with dots."""
        from pydantic import BaseModel, ValidationError

        class _Inner(BaseModel):
            nested_value: int

        class _Outer(BaseModel):
            inner: _Inner

        try:
            _Outer.model_validate({"inner": {"nested_value": "bad"}})
        except ValidationError as ve:
            mock_guard_struct.from_json.side_effect = ve

        with self.assertRaises(HttpError) as ctx:
            await get_guard_body(self._make_request("GET", {"name": "test"}))

        error = ctx.exception
        self.assertIsNotNone(error.fields)
        self.assertIn("inner.nested_value", error.fields)  # type: ignore[arg-type]

    async def test_validation_error_empty_loc_uses_dollar_path(self):
        """Test that an error with empty loc tuple maps to '$' path."""

        class _FakeValidationError(Exception):
            def errors(self):
                return [{"loc": (), "msg": "root-level error", "type": "value_error"}]

        with (
            patch("guardrails_api.api.guards.ValidationError", _FakeValidationError),
            patch("guardrails_api.api.guards.GuardStruct") as mock_guard_struct,
        ):
            mock_guard_struct.from_json.side_effect = _FakeValidationError()

            with self.assertRaises(HttpError) as ctx:
                await get_guard_body(self._make_request("GET", {"name": "test"}))

        error = ctx.exception
        self.assertEqual(error.status, 400)
        self.assertIsNotNone(error.fields)
        self.assertIn("$", error.fields)  # type: ignore[arg-type]
        self.assertEqual(error.fields["$"], "root-level error")  # type: ignore[index]

    async def test_validation_error_multiple_errors_all_mapped(self):
        """Test that all errors from a ValidationError are mapped into fields."""

        class _FakeValidationError(Exception):
            def errors(self):
                return [
                    {"loc": ("field_a",), "msg": "error a", "type": "value_error"},
                    {"loc": ("field_b",), "msg": "error b", "type": "value_error"},
                ]

        with (
            patch("guardrails_api.api.guards.ValidationError", _FakeValidationError),
            patch("guardrails_api.api.guards.GuardStruct") as mock_guard_struct,
        ):
            mock_guard_struct.from_json.side_effect = _FakeValidationError()

            with self.assertRaises(HttpError) as ctx:
                await get_guard_body(self._make_request("PUT", {"name": "test"}))

        error = ctx.exception
        self.assertEqual(error.status, 400)
        self.assertIsNotNone(error.fields)
        self.assertIn("field_a", error.fields)  # type: ignore[arg-type]
        self.assertIn("field_b", error.fields)  # type: ignore[arg-type]
        self.assertEqual(error.fields["field_a"], "error a")  # type: ignore[index]
        self.assertEqual(error.fields["field_b"], "error b")  # type: ignore[index]

    async def test_validation_error_mixed_loc_types_stringified(self):
        """Test that integer indices in loc are stringified and joined."""

        class _FakeValidationError(Exception):
            def errors(self):
                return [
                    {"loc": ("items", 0, "value"), "msg": "bad", "type": "value_error"}
                ]

        with (
            patch("guardrails_api.api.guards.ValidationError", _FakeValidationError),
            patch("guardrails_api.api.guards.GuardStruct") as mock_guard_struct,
        ):
            mock_guard_struct.from_json.side_effect = _FakeValidationError()

            with self.assertRaises(HttpError) as ctx:
                await get_guard_body(self._make_request("GET", {"name": "test"}))

        error = ctx.exception
        self.assertIsNotNone(error.fields)
        self.assertIn("items.0.value", error.fields)  # type: ignore[arg-type]


class TestGuardsModule(unittest.TestCase):
    """Test cases for guards module level functionality."""

    def test_module_has_router(self):
        """Test that guards module exports a router."""
        from guardrails_api.api import guards

        self.assertTrue(hasattr(guards, "router"))

    def test_module_has_get_guard_client(self):
        """Test that guards module has get_guard_client function."""
        from guardrails_api.api import guards

        self.assertTrue(hasattr(guards, "get_guard_client"))
        self.assertTrue(callable(guards.get_guard_client))

    def test_module_has_cache_client(self):
        """Test that guards module has cache_client initialized."""
        from guardrails_api.api import guards

        self.assertTrue(hasattr(guards, "cache_client"))


if __name__ == "__main__":
    unittest.main()
