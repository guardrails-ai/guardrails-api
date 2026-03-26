"""Unit tests for guardrails_api.api.guards module."""

import json
import unittest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from guardrails import Guard
from guardrails_ai.types import Guard as IGuard
from guardrails_api.api.guards import router, guard_history_is_enabled, to_IGuard


class TestGuardHistoryIsEnabled(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_enabled_by_default(self):
        self.assertTrue(guard_history_is_enabled())

    @patch.dict("os.environ", {"GUARD_HISTORY_ENABLED": "true"})
    def test_enabled_when_true(self):
        self.assertTrue(guard_history_is_enabled())

    @patch.dict("os.environ", {"GUARD_HISTORY_ENABLED": "True"})
    def test_enabled_case_insensitive(self):
        self.assertTrue(guard_history_is_enabled())

    @patch.dict("os.environ", {"GUARD_HISTORY_ENABLED": "false"})
    def test_disabled_when_false(self):
        self.assertFalse(guard_history_is_enabled())

    @patch.dict("os.environ", {"GUARD_HISTORY_ENABLED": "FALSE"})
    def test_disabled_case_insensitive(self):
        self.assertFalse(guard_history_is_enabled())

    @patch.dict("os.environ", {"GUARD_HISTORY_ENABLED": "invalid"})
    def test_disabled_with_invalid_value(self):
        self.assertFalse(guard_history_is_enabled())


class TestToIGuard(unittest.TestCase):
    def test_iguard_returned_as_is(self):
        """IGuard instances pass through unchanged."""
        iguard = IGuard(name="test", id="test-id")
        result = to_IGuard(iguard)
        self.assertIs(result, iguard)

    @patch("guardrails_api.api.guards.IGuard")
    def test_guard_instance_converted_via_model_validate(self, mock_iguard_class):
        """Guard instances are converted via model_dump -> IGuard.model_validate."""
        mock_guard = Mock(spec=Guard)
        mock_guard.model_dump.return_value = {"name": "test", "id": "test-id"}
        expected = Mock()
        mock_iguard_class.model_validate.return_value = expected

        result = to_IGuard(mock_guard)

        mock_guard.model_dump.assert_called_once_with(exclude_none=True)
        mock_iguard_class.model_validate.assert_called_once_with(
            {"name": "test", "id": "test-id"}
        )
        self.assertIs(result, expected)


class TestGuardsAPI(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    # --- GET /guards ---

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guards_empty_list(self, mock_get_gc):
        mock_gc = Mock()
        mock_gc.get_guards.return_value = []
        mock_get_gc.return_value = mock_gc

        response = self.client.get("/guards")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guards_returns_iguard_list(self, mock_get_gc):
        guard1 = IGuard(name="guard1", id="guard-1")
        guard2 = IGuard(name="guard2", id="guard-2")
        mock_gc = Mock()
        mock_gc.get_guards.return_value = [guard1, guard2]
        mock_get_gc.return_value = mock_gc

        response = self.client.get("/guards")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        names = {g["name"] for g in data}
        self.assertEqual(names, {"guard1", "guard2"})

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guards_without_name_passes_none(self, mock_get_gc):
        mock_gc = Mock()
        mock_gc.get_guards.return_value = []
        mock_get_gc.return_value = mock_gc

        self.client.get("/guards")

        mock_gc.get_guards.assert_called_once_with(guard_name=None)

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guards_url_decodes_name(self, mock_get_gc):
        mock_gc = Mock()
        mock_gc.get_guards.return_value = []
        mock_get_gc.return_value = mock_gc

        self.client.get("/guards?name=my+guard")

        mock_gc.get_guards.assert_called_once_with(guard_name="my guard")

    # --- POST /guards ---

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_create_guard_501_without_postgres(self, mock_get_gc, mock_pg):
        mock_pg.return_value = False
        mock_get_gc.return_value = Mock()

        response = self.client.post("/guards", json={"name": "my_guard"})

        self.assertEqual(response.status_code, 501)
        self.assertIn("Not Implemented", response.json()["detail"])

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_create_guard_success(self, mock_get_gc, mock_pg):
        mock_pg.return_value = True
        new_guard = IGuard(name="my_guard", id="my-guard")
        mock_gc = Mock()
        mock_gc.create_guard.return_value = new_guard
        mock_get_gc.return_value = mock_gc

        response = self.client.post("/guards", json={"name": "my_guard"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "my_guard")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_create_guard_invalid_payload_returns_422(self, mock_get_gc, mock_pg):
        mock_pg.return_value = True
        mock_get_gc.return_value = Mock()

        response = self.client.post("/guards", json={})

        self.assertEqual(response.status_code, 422)

    # --- GET /guards/{id} ---

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_not_found_returns_404(self, mock_get_gc):
        mock_gc = Mock()
        mock_gc.get_guard.return_value = None
        mock_get_gc.return_value = mock_gc

        response = self.client.get("/guards/nonexistent")

        self.assertEqual(response.status_code, 404)
        self.assertIn("does not exist", response.json()["detail"])

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_success(self, mock_get_gc):
        guard = IGuard(name="test_guard", id="test-guard")
        mock_gc = Mock()
        mock_gc.get_guard.return_value = guard
        mock_get_gc.return_value = mock_gc

        response = self.client.get("/guards/test-guard")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "test_guard")

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_url_decodes_id(self, mock_get_gc):
        guard = IGuard(name="test guard", id="test-guard")
        mock_gc = Mock()
        mock_gc.get_guard.return_value = guard
        mock_get_gc.return_value = mock_gc

        self.client.get("/guards/test+guard")

        mock_gc.get_guard.assert_called_once_with("test guard", None)

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_passes_as_of(self, mock_get_gc):
        guard = IGuard(name="test_guard", id="test-guard")
        mock_gc = Mock()
        mock_gc.get_guard.return_value = guard
        mock_get_gc.return_value = mock_gc

        self.client.get("/guards/test-guard?asOf=2024-01-01")

        mock_gc.get_guard.assert_called_once_with("test-guard", "2024-01-01")

    # --- PUT /guards/{id} ---

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_update_guard_501_without_postgres(self, mock_get_gc, mock_pg):
        mock_pg.return_value = False
        mock_get_gc.return_value = Mock()

        response = self.client.put(
            "/guards/test-guard", json={"name": "test_guard", "id": "test-guard"}
        )

        self.assertEqual(response.status_code, 501)
        self.assertIn("not implemented", response.json()["detail"])

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_update_guard_success(self, mock_get_gc, mock_pg):
        mock_pg.return_value = True
        updated = IGuard(name="test_guard", id="test-guard")
        mock_gc = Mock()
        mock_gc.upsert_guard.return_value = updated
        mock_get_gc.return_value = mock_gc

        response = self.client.put(
            "/guards/test-guard", json={"name": "test_guard", "id": "test-guard"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "test_guard")
        mock_gc.upsert_guard.assert_called_once()
        call_id_arg = mock_gc.upsert_guard.call_args[0][0]
        self.assertEqual(call_id_arg, "test-guard")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_update_guard_url_decodes_id(self, mock_get_gc, mock_pg):
        mock_pg.return_value = True
        updated = IGuard(name="test guard", id="test-guard")
        mock_gc = Mock()
        mock_gc.upsert_guard.return_value = updated
        mock_get_gc.return_value = mock_gc

        self.client.put(
            "/guards/test+guard", json={"name": "test guard", "id": "test-guard"}
        )

        call_id_arg = mock_gc.upsert_guard.call_args[0][0]
        self.assertEqual(call_id_arg, "test guard")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_update_guard_invalid_payload_returns_422(self, mock_get_gc, mock_pg):
        mock_pg.return_value = True
        mock_get_gc.return_value = Mock()

        response = self.client.put("/guards/test-guard", json={})

        self.assertEqual(response.status_code, 422)

    # --- DELETE /guards/{id} ---

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_delete_guard_501_without_postgres(self, mock_get_gc, mock_pg):
        mock_pg.return_value = False
        mock_get_gc.return_value = Mock()

        response = self.client.delete("/guards/test-guard")

        self.assertEqual(response.status_code, 501)
        self.assertIn("not implemented", response.json()["detail"])

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_delete_guard_success(self, mock_get_gc, mock_pg):
        mock_pg.return_value = True
        guard = IGuard(name="test_guard", id="test-guard")
        mock_gc = Mock()
        mock_gc.delete_guard.return_value = guard
        mock_get_gc.return_value = mock_gc

        response = self.client.delete("/guards/test-guard")

        self.assertEqual(response.status_code, 200)
        mock_gc.delete_guard.assert_called_once_with("test-guard")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.get_guard_client")
    def test_delete_guard_url_decodes_id(self, mock_get_gc, mock_pg):
        mock_pg.return_value = True
        guard = IGuard(name="test guard", id="test-guard")
        mock_gc = Mock()
        mock_gc.delete_guard.return_value = guard
        mock_get_gc.return_value = mock_gc

        self.client.delete("/guards/test+guard")

        mock_gc.delete_guard.assert_called_once_with("test guard")

    # --- POST /guards/{id}/openai/v1/chat/completions ---

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_openai_completions_guard_not_found(self, mock_get_gc):
        mock_gc = Mock()
        mock_gc.get_guard.return_value = None
        mock_get_gc.return_value = mock_gc

        response = self.client.post(
            "/guards/nonexistent/openai/v1/chat/completions",
            json={"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]},
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("does not exist", response.json()["detail"])

    # --- GET /guards/{id}/history/{call_id} ---

    @patch("guardrails_api.api.guards.cache_client")
    def test_guard_history_returns_200_with_cached_value(self, mock_cache):
        # Cache returns a serialized list; FastAPI validates it as list[Call]
        mock_cache.get = AsyncMock(return_value=json.dumps([{}]))

        response = self.client.get("/guards/test-guard/history/call-123")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(len(response.json()), 1)

    @patch("guardrails_api.api.guards.cache_client")
    def test_guard_history_returns_empty_list_when_not_cached(self, mock_cache):
        mock_cache.get = AsyncMock(return_value=None)

        response = self.client.get("/guards/test-guard/history/call-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    # --- Router structure ---

    def test_all_expected_routes_registered(self):
        routes = {route.path for route in self.app.routes}
        expected = {
            "/guards",
            "/guards/{id}",
            "/guards/{id}/openai/v1/chat/completions",
            "/guards/{id}/validate",
            "/guards/{id}/history/{call_id}",
        }
        self.assertTrue(expected.issubset(routes))

    def test_guards_route_has_get_and_post(self):
        methods = set()
        for route in self.app.routes:
            if route.path == "/guards" and hasattr(route, "methods"):
                methods.update(route.methods)
        self.assertIn("GET", methods)
        self.assertIn("POST", methods)

    def test_guard_id_route_has_get_put_delete(self):
        methods = set()
        for route in self.app.routes:
            if route.path == "/guards/{id}" and hasattr(route, "methods"):
                methods.update(route.methods)
        self.assertIn("GET", methods)
        self.assertIn("PUT", methods)
        self.assertIn("DELETE", methods)


if __name__ == "__main__":
    unittest.main()
