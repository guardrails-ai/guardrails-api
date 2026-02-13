"""Unit tests for guardrails_api.api.guards module."""

import unittest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from guardrails_api.api.guards import router, guard_history_is_enabled


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

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guards(self, mock_get_guard_client):
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

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guards_empty_list(self, mock_get_guard_client):
        """Test GET /guards when no guards exist."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard_client.get_guards.return_value = []

        response = self.client.get("/guards")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    def test_create_guard_not_implemented_for_memory(self, mock_postgres):
        """Test POST /guards fails for in-memory guards."""
        mock_postgres.return_value = False

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

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_success(self, mock_get_guard_client):
        """Test GET /guards/{guard_name} successfully retrieves a guard."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard = Mock()
        mock_guard.to_dict.return_value = {"name": "test_guard", "description": "Test"}
        mock_guard_client.get_guard.return_value = mock_guard

        response = self.client.get("/guards/test_guard")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "test_guard")

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_not_found(self, mock_get_guard_client):
        """Test GET /guards/{guard_name} returns 404 when guard not found."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard_client.get_guard.return_value = None

        response = self.client.get("/guards/nonexistent")

        self.assertEqual(response.status_code, 404)
        self.assertIn("does not exist", response.json()["detail"])

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_url_encoded_name(self, mock_get_guard_client):
        """Test GET /guards/{guard_name} handles URL-encoded names."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard = Mock()
        mock_guard.to_dict.return_value = {"name": "test guard", "description": "Test"}
        mock_guard_client.get_guard.return_value = mock_guard

        # "test guard" URL encoded is "test+guard"
        response = self.client.get("/guards/test+guard")

        self.assertEqual(response.status_code, 200)
        # Verify the decoded name was passed to get_guard
        mock_guard_client.get_guard.assert_called_once_with("test guard", None)

    @patch("guardrails_api.api.guards.get_guard_client")
    def test_get_guard_with_as_of_date(self, mock_get_guard_client):
        """Test GET /guards/{guard_name} with asOf parameter."""
        mock_guard_client = Mock()
        mock_get_guard_client.return_value = mock_guard_client

        mock_guard = Mock()
        mock_guard.to_dict.return_value = {"name": "test_guard"}
        mock_guard_client.get_guard.return_value = mock_guard

        response = self.client.get("/guards/test_guard?asOf=2024-01-01")

        self.assertEqual(response.status_code, 200)
        mock_guard_client.get_guard.assert_called_once_with("test_guard", "2024-01-01")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    def test_update_guard_not_implemented_for_memory(self, mock_postgres):
        """Test PUT /guards/{guard_name} fails for in-memory guards."""
        mock_postgres.return_value = False

        response = self.client.put(
            "/guards/test_guard", json={"name": "test_guard", "description": "Updated"}
        )

        self.assertEqual(response.status_code, 501)
        self.assertIn("not implemented", response.json()["detail"])

    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.GuardStruct")
    def test_update_guard_success(
        self, mock_guard_struct_class, mock_postgres, mock_get_guard_client
    ):
        """Test PUT /guards/{guard_name} successfully updates a guard."""
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
            "/guards/test_guard", json={"name": "test_guard", "description": "Updated"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["description"], "Updated")

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    def test_delete_guard_not_implemented_for_memory(self, mock_postgres):
        """Test DELETE /guards/{guard_name} fails for in-memory guards."""
        mock_postgres.return_value = False

        response = self.client.delete("/guards/test_guard")

        self.assertEqual(response.status_code, 501)
        self.assertIn("not implemented", response.json()["detail"])

    @patch("guardrails_api.api.guards.get_guard_client")
    @patch("guardrails_api.api.guards.postgres_is_enabled")
    def test_delete_guard_success(self, mock_postgres, mock_get_guard_client):
        """Test DELETE /guards/{guard_name} successfully deletes a guard."""
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
        self.assertIn("/guards/{guard_name}/validate", routes)

    @patch("guardrails_api.api.guards.cache_client")
    def test_guard_history_endpoint(self, mock_cache_client):
        """Test GET /guards/{guard_name}/history/{call_id} endpoint."""
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
            "/guards/{guard_name}",
            "/guards/{guard_name}/openai/v1/chat/completions",
            "/guards/{guard_name}/validate",
            "/guards/{guard_name}/history/{call_id}",
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

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.GuardStruct")
    def test_create_guard_invalid_payload(self, mock_guard_struct, mock_postgres):
        """Test POST /guards with invalid payload returns 422."""
        mock_postgres.return_value = True
        mock_guard_struct.from_json.return_value = None

        response = self.client.post("/guards", json={})

        self.assertEqual(response.status_code, 422)

    @patch("guardrails_api.api.guards.postgres_is_enabled")
    @patch("guardrails_api.api.guards.GuardStruct")
    def test_update_guard_invalid_payload(self, mock_guard_struct, mock_postgres):
        """Test PUT /guards/{guard_name} with invalid payload returns 422."""
        mock_postgres.return_value = True
        mock_guard_struct.from_json.return_value = None

        response = self.client.put("/guards/test_guard", json={})

        self.assertEqual(response.status_code, 422)


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
