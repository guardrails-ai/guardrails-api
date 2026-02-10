"""Unit tests for guardrails_api.api.root module."""
import unittest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from guardrails_api.api.root import router, HealthCheckResponse


class TestRootAPI(unittest.TestCase):
    """Test cases for the root API module."""

    def setUp(self):
        """Set up test client."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_home_endpoint(self):
        """Test the home endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Hello, world!")

    @patch('guardrails_api.api.root.postgres_is_enabled')
    def test_health_check_without_postgres(self, mock_postgres_enabled):
        """Test health check when postgres is disabled."""
        mock_postgres_enabled.return_value = False

        response = self.client.get("/health-check")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["message"], "Ok")

    @patch('guardrails_api.api.root.logger')
    @patch('guardrails_api.api.root.PostgresClient')
    @patch('guardrails_api.api.root.postgres_is_enabled')
    def test_health_check_with_postgres(
        self, mock_postgres_enabled, mock_pg_client_class, mock_logger
    ):
        """Test health check when postgres is enabled."""
        mock_postgres_enabled.return_value = True

        mock_session = Mock()
        mock_session.execute.return_value.all.return_value = [(5,)]

        mock_pg_client = Mock()
        mock_pg_client.SessionLocal.return_value = mock_session
        mock_pg_client_class.return_value = mock_pg_client

        response = self.client.get("/health-check")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["message"], "Ok")

    @patch('guardrails_api.api.root.logger')
    @patch('guardrails_api.api.root.PostgresClient')
    @patch('guardrails_api.api.root.postgres_is_enabled')
    def test_health_check_postgres_error(
        self, mock_postgres_enabled, mock_pg_client_class, mock_logger
    ):
        """Test health check when postgres connection fails."""
        mock_postgres_enabled.return_value = True

        mock_pg_client = Mock()
        mock_pg_client.SessionLocal.side_effect = Exception("Connection failed")
        mock_pg_client_class.return_value = mock_pg_client

        response = self.client.get("/health-check")

        self.assertEqual(response.status_code, 500)
        mock_logger.error.assert_called()

    @patch('guardrails_api.api.root.get_open_api_spec')
    def test_api_docs_endpoint(self, mock_get_spec):
        """Test the API docs endpoint."""
        mock_spec = {"openapi": "3.0.0", "info": {"title": "Test API"}}
        mock_get_spec.return_value = mock_spec

        response = self.client.get("/api-docs")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mock_spec)
        mock_get_spec.assert_called_once()

    def test_docs_endpoint_exists(self):
        """Test the docs endpoint is available."""
        response = self.client.get("/docs")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])


class TestHealthCheckResponse(unittest.TestCase):
    """Test cases for HealthCheckResponse model."""

    def test_health_check_response_model(self):
        """Test HealthCheckResponse Pydantic model."""
        response = HealthCheckResponse(status=200, message="Ok")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.message, "Ok")

    def test_health_check_response_validation(self):
        """Test HealthCheckResponse validates required fields."""
        with self.assertRaises(Exception):
            HealthCheckResponse()


if __name__ == "__main__":
    unittest.main()
