"""Unit tests for guardrails_api.otel.metrics module."""

import unittest
from unittest.mock import patch, Mock
from guardrails_api.otel.metrics import (
    metrics_are_disabled,
    get_meter,
    get_metrics_exporter,
    initialize_metrics_collector,
)


class TestMetricsAreDisabled(unittest.TestCase):
    """Test cases for the metrics_are_disabled function."""

    @patch.dict("os.environ", {}, clear=True)
    def test_metrics_disabled_by_default(self):
        """Test that metrics are disabled when no env var is set."""
        result = metrics_are_disabled()
        self.assertTrue(result)

    @patch.dict("os.environ", {"OTEL_METRICS_EXPORTER": "none"})
    def test_metrics_disabled_when_set_to_none(self):
        """Test that metrics are disabled when set to 'none'."""
        result = metrics_are_disabled()
        self.assertTrue(result)

    @patch.dict("os.environ", {"OTEL_METRICS_EXPORTER": "otlp"})
    def test_metrics_enabled_when_set_to_otlp(self):
        """Test that metrics are enabled when set to 'otlp'."""
        result = metrics_are_disabled()
        self.assertFalse(result)


class TestGetMeter(unittest.TestCase):
    """Test cases for the get_meter function."""

    @patch("guardrails_api.otel.metrics.metrics.get_meter")
    @patch.dict("os.environ", {}, clear=True)
    def test_get_meter_default_name(self, mock_get_meter):
        """Test get_meter with default service name."""
        mock_meter = Mock()
        mock_get_meter.return_value = mock_meter

        result = get_meter()

        mock_get_meter.assert_called_once_with("guardrails-api")
        self.assertEqual(result, mock_meter)

    @patch("guardrails_api.otel.metrics.metrics.get_meter")
    @patch.dict("os.environ", {"OTEL_SERVICE_NAME": "custom-service"})
    def test_get_meter_custom_service_name(self, mock_get_meter):
        """Test get_meter with custom service name from env."""
        mock_meter = Mock()
        mock_get_meter.return_value = mock_meter

        result = get_meter()

        mock_get_meter.assert_called_once_with("custom-service")
        self.assertEqual(result, mock_meter)

    @patch("guardrails_api.otel.metrics.metrics.get_meter")
    def test_get_meter_with_explicit_name(self, mock_get_meter):
        """Test get_meter with explicitly provided name."""
        mock_meter = Mock()
        mock_get_meter.return_value = mock_meter

        result = get_meter("my-meter")

        mock_get_meter.assert_called_once_with("my-meter")
        assert result == mock_meter


class TestGetMetricsExporter(unittest.TestCase):
    """Test cases for the get_metrics_exporter function."""

    @patch.dict("os.environ", {"OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf"})
    @patch("guardrails_api.otel.metrics.HttpMetricExporter")
    def test_get_metrics_exporter_otlp_http(self, mock_http_exporter):
        """Test getting OTLP HTTP metrics exporter."""
        mock_exporter = Mock()
        mock_http_exporter.return_value = mock_exporter

        result = get_metrics_exporter("otlp")

        mock_http_exporter.assert_called_once()
        self.assertEqual(result, mock_exporter)

    @patch.dict("os.environ", {"OTEL_EXPORTER_OTLP_PROTOCOL": "grpc"})
    @patch("guardrails_api.otel.metrics.GrpcMetricExporter")
    def test_get_metrics_exporter_otlp_grpc(self, mock_grpc_exporter):
        """Test getting OTLP gRPC metrics exporter."""
        mock_exporter = Mock()
        mock_grpc_exporter.return_value = mock_exporter

        result = get_metrics_exporter("otlp")

        mock_grpc_exporter.assert_called_once()
        self.assertEqual(result, mock_exporter)

    @patch("guardrails_api.otel.metrics.ConsoleMetricExporter")
    def test_get_metrics_exporter_console(self, mock_console_exporter):
        """Test getting console metrics exporter."""
        mock_exporter = Mock()
        mock_console_exporter.return_value = mock_exporter

        result = get_metrics_exporter("console")

        mock_console_exporter.assert_called_once()
        self.assertEqual(result, mock_exporter)


class TestInitializeMetricsCollector(unittest.TestCase):
    """Test cases for the initialize_metrics_collector function."""

    @patch("guardrails_api.otel.metrics.metrics_are_disabled")
    def test_initialize_skipped_when_disabled(self, mock_disabled):
        """Test that initialization is skipped when metrics are disabled."""
        mock_disabled.return_value = True

        # Should not raise any errors
        initialize_metrics_collector()

        mock_disabled.assert_called_once()

    @patch("guardrails_api.otel.metrics.get_meter")
    @patch("guardrails_api.otel.metrics.metrics.set_meter_provider")
    @patch("guardrails_api.otel.metrics.MeterProvider")
    @patch("guardrails_api.otel.metrics.PeriodicExportingMetricReader")
    @patch("guardrails_api.otel.metrics.get_metrics_exporter")
    @patch("guardrails_api.otel.metrics.metrics_are_disabled")
    @patch.dict("os.environ", {"OTEL_METRICS_EXPORTER": "console"})
    def test_initialize_with_console_exporter(
        self,
        mock_disabled,
        mock_get_exporter,
        mock_reader_class,
        mock_provider_class,
        mock_set_provider,
        mock_get_meter,
    ):
        """Test initialization with console exporter."""
        mock_disabled.return_value = False
        mock_exporter = Mock()
        mock_get_exporter.return_value = mock_exporter
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider

        initialize_metrics_collector()

        mock_get_exporter.assert_called_with("console")
        mock_reader_class.assert_called_once_with(mock_exporter)
        mock_provider_class.assert_called_once()
        mock_set_provider.assert_called_once_with(mock_provider)
        mock_get_meter.assert_called_once()


if __name__ == "__main__":
    unittest.main()
