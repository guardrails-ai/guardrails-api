"""Unit tests for guardrails_api.otel.traces module."""

import unittest
from unittest.mock import patch, Mock
from guardrails_api.otel.traces import (
    traces_are_disabled,
    get_tracer,
    get_span_exporter,
    set_span_processors,
    initialize_tracer,
)


class TestTracesAreDisabled(unittest.TestCase):
    """Test cases for the traces_are_disabled function."""

    @patch.dict("os.environ", {}, clear=True)
    def test_traces_disabled_by_default(self):
        """Test that traces are disabled when no env var is set."""
        result = traces_are_disabled()
        self.assertTrue(result)

    @patch.dict("os.environ", {"OTEL_TRACES_EXPORTER": "none"})
    def test_traces_disabled_when_set_to_none(self):
        """Test that traces are disabled when set to 'none'."""
        result = traces_are_disabled()
        self.assertTrue(result)

    @patch.dict("os.environ", {"OTEL_TRACES_EXPORTER": "otlp"})
    def test_traces_enabled_when_set_to_otlp(self):
        """Test that traces are enabled when set to 'otlp'."""
        result = traces_are_disabled()
        self.assertFalse(result)


class TestGetTracer(unittest.TestCase):
    """Test cases for the get_tracer function."""

    @patch("guardrails_api.otel.traces.trace.get_tracer")
    @patch.dict("os.environ", {}, clear=True)
    def test_get_tracer_default_name(self, mock_get_tracer):
        """Test get_tracer with default service name."""
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        result = get_tracer()

        mock_get_tracer.assert_called_once_with("guardrails-api")
        self.assertEqual(result, mock_tracer)

    @patch("guardrails_api.otel.traces.trace.get_tracer")
    @patch.dict("os.environ", {"OTEL_SERVICE_NAME": "custom-service"})
    def test_get_tracer_custom_service_name(self, mock_get_tracer):
        """Test get_tracer with custom service name from env."""
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        result = get_tracer()

        mock_get_tracer.assert_called_once_with("custom-service")
        self.assertEqual(result, mock_tracer)

    @patch("guardrails_api.otel.traces.trace.get_tracer")
    def test_get_tracer_with_explicit_name(self, mock_get_tracer):
        """Test get_tracer with explicitly provided name."""
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        result = get_tracer("my-tracer")

        mock_get_tracer.assert_called_once_with("my-tracer")
        assert result == mock_tracer


class TestGetSpanExporter(unittest.TestCase):
    """Test cases for the get_span_exporter function."""

    @patch.dict("os.environ", {"OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf"})
    @patch("guardrails_api.otel.traces.HttpSpanExporter")
    def test_get_span_exporter_otlp_http(self, mock_http_exporter):
        """Test getting OTLP HTTP span exporter."""
        mock_exporter = Mock()
        mock_http_exporter.return_value = mock_exporter

        result = get_span_exporter("otlp")

        mock_http_exporter.assert_called_once()
        self.assertEqual(result, mock_exporter)

    @patch.dict("os.environ", {"OTEL_EXPORTER_OTLP_PROTOCOL": "grpc"})
    @patch("guardrails_api.otel.traces.GrpcSpanExporter")
    def test_get_span_exporter_otlp_grpc(self, mock_grpc_exporter):
        """Test getting OTLP gRPC span exporter."""
        mock_exporter = Mock()
        mock_grpc_exporter.return_value = mock_exporter

        result = get_span_exporter("otlp")

        mock_grpc_exporter.assert_called_once()
        self.assertEqual(result, mock_exporter)

    @patch("guardrails_api.otel.traces.ConsoleSpanExporter")
    def test_get_span_exporter_console(self, mock_console_exporter):
        """Test getting console span exporter."""
        mock_exporter = Mock()
        mock_console_exporter.return_value = mock_exporter

        result = get_span_exporter("console")

        mock_console_exporter.assert_called_once()
        self.assertEqual(result, mock_exporter)


class TestSetSpanProcessors(unittest.TestCase):
    """Test cases for the set_span_processors function."""

    @patch("guardrails_api.otel.traces.BatchSpanProcessor")
    def test_set_span_processors_with_batch(self, mock_batch_processor):
        """Test setting span processors with batch processing."""
        mock_provider = Mock()
        mock_exporter = Mock()
        mock_processor = Mock()
        mock_batch_processor.return_value = mock_processor

        set_span_processors(mock_provider, mock_exporter, use_batch=True)

        mock_batch_processor.assert_called_once_with(mock_exporter)
        mock_provider.add_span_processor.assert_called_once_with(mock_processor)

    @patch("guardrails_api.otel.traces.SimpleSpanProcessor")
    def test_set_span_processors_without_batch(self, mock_simple_processor):
        """Test setting span processors without batch processing."""
        mock_provider = Mock()
        mock_exporter = Mock()
        mock_processor = Mock()
        mock_simple_processor.return_value = mock_processor

        set_span_processors(mock_provider, mock_exporter, use_batch=False)

        mock_simple_processor.assert_called_once_with(mock_exporter)
        mock_provider.add_span_processor.assert_called_once_with(mock_processor)


class TestInitializeTracer(unittest.TestCase):
    """Test cases for the initialize_tracer function."""

    @patch("guardrails_api.otel.traces.traces_are_disabled")
    def test_initialize_skipped_when_disabled(self, mock_disabled):
        """Test that initialization is skipped when traces are disabled."""
        mock_disabled.return_value = True

        # Should not raise any errors
        initialize_tracer()

        mock_disabled.assert_called_once()

    @patch("guardrails_api.otel.traces.get_tracer")
    @patch("guardrails_api.otel.traces.set_span_processors")
    @patch("guardrails_api.otel.traces.get_span_exporter")
    @patch("guardrails_api.otel.traces.trace.get_tracer_provider")
    @patch("guardrails_api.otel.traces.traces_are_disabled")
    @patch.dict(
        "os.environ",
        {"OTEL_TRACES_EXPORTER": "console", "OTEL_PROCESS_IN_BATCH": "true"},
    )
    def test_initialize_with_console_exporter(
        self,
        mock_disabled,
        mock_get_provider,
        mock_get_exporter,
        mock_set_processors,
        mock_get_tracer,
    ):
        """Test initialization with console exporter."""
        mock_disabled.return_value = False
        mock_provider = Mock()
        mock_get_provider.return_value = mock_provider
        mock_exporter = Mock()
        mock_get_exporter.return_value = mock_exporter

        initialize_tracer()

        mock_get_exporter.assert_called_with("console")
        mock_set_processors.assert_called_once_with(mock_provider, mock_exporter, True)
        mock_get_tracer.assert_called_once()

    @patch("guardrails_api.otel.traces.get_tracer")
    @patch("guardrails_api.otel.traces.set_span_processors")
    @patch("guardrails_api.otel.traces.get_span_exporter")
    @patch("guardrails_api.otel.traces.trace.get_tracer_provider")
    @patch("guardrails_api.otel.traces.traces_are_disabled")
    @patch.dict(
        "os.environ",
        {"OTEL_TRACES_EXPORTER": "console", "OTEL_PROCESS_IN_BATCH": "false"},
    )
    def test_initialize_without_batch(
        self,
        mock_disabled,
        mock_get_provider,
        mock_get_exporter,
        mock_set_processors,
        mock_get_tracer,
    ):
        """Test initialization without batch processing."""
        mock_disabled.return_value = False
        mock_provider = Mock()
        mock_get_provider.return_value = mock_provider
        mock_exporter = Mock()
        mock_get_exporter.return_value = mock_exporter

        initialize_tracer()

        mock_set_processors.assert_called_once_with(mock_provider, mock_exporter, False)


if __name__ == "__main__":
    unittest.main()
