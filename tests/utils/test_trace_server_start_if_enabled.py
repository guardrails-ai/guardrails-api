"""Unit tests for guardrails_api.utils.trace_server_start_if_enabled module."""
import unittest
from unittest.mock import patch, Mock
from guardrails_api.utils.trace_server_start_if_enabled import trace_server_start_if_enabled


class TestTraceServerStartIfEnabled(unittest.TestCase):
    """Test cases for the trace_server_start_if_enabled function."""

    @patch('guardrails_api.utils.trace_server_start_if_enabled.has_internet_connection')
    @patch('guardrails_api.utils.trace_server_start_if_enabled.Credentials')
    def test_trace_server_disabled(self, mock_credentials, mock_internet):
        """Test that tracing is skipped when metrics are disabled."""
        mock_config = Mock()
        mock_config.enable_metrics = False
        mock_credentials.from_rc_file.return_value = mock_config
        mock_internet.return_value = True

        # Should not raise any errors and should not attempt import
        trace_server_start_if_enabled()

        mock_credentials.from_rc_file.assert_called_once()

    @patch('guardrails_api.utils.trace_server_start_if_enabled.has_internet_connection')
    @patch('guardrails_api.utils.trace_server_start_if_enabled.Credentials')
    def test_trace_server_no_internet(self, mock_credentials, mock_internet):
        """Test that tracing is skipped when there's no internet connection."""
        mock_config = Mock()
        mock_config.enable_metrics = True
        mock_credentials.from_rc_file.return_value = mock_config
        mock_internet.return_value = False

        # Should not raise any errors and should not attempt import
        trace_server_start_if_enabled()

        mock_credentials.from_rc_file.assert_called_once()
        mock_internet.assert_called_once()

    @patch('guardrails_api.utils.trace_server_start_if_enabled.has_internet_connection')
    @patch('guardrails_api.utils.trace_server_start_if_enabled.Credentials')
    @patch('guardrails_api.utils.trace_server_start_if_enabled.platform')
    @patch('guardrails_api.utils.trace_server_start_if_enabled.GUARDRAILS_VERSION', '0.1.0')
    def test_trace_server_enabled_with_internet(
        self, mock_platform, mock_credentials, mock_internet
    ):
        """Test that tracing is initiated when enabled and internet is available."""
        # Setup mocks
        mock_config = Mock()
        mock_config.enable_metrics = True
        mock_credentials.from_rc_file.return_value = mock_config
        mock_internet.return_value = True

        mock_platform.python_version.return_value = "3.11.0"
        mock_platform.system.return_value = "Linux"
        mock_platform.platform.return_value = "Linux-5.15.0"
        mock_platform.architecture.return_value = ("64bit", "ELF")
        mock_platform.machine.return_value = "x86_64"
        mock_platform.processor.return_value = "x86_64"

        # Mock HubTelemetry at the point where it's imported
        with patch('guardrails.utils.hub_telemetry_utils.HubTelemetry') as mock_hub:
            mock_telemetry_instance = Mock()
            mock_hub.return_value = mock_telemetry_instance

            trace_server_start_if_enabled()

            mock_hub.assert_called_once()
            mock_telemetry_instance.create_new_span.assert_called_once()

            # Verify the span was created with correct parameters
            call_args = mock_telemetry_instance.create_new_span.call_args
            self.assertEqual(call_args[0][0], "guardrails-api/start")

            # Verify attributes contain expected values
            attributes = call_args[0][1]
            attribute_dict = dict(attributes)
            self.assertEqual(attribute_dict["guardrails-version"], "0.1.0")
            self.assertEqual(attribute_dict["python-version"], "3.11.0")
            self.assertEqual(attribute_dict["system"], "Linux")

    @patch('guardrails_api.utils.trace_server_start_if_enabled.has_internet_connection')
    @patch('guardrails_api.utils.trace_server_start_if_enabled.Credentials')
    def test_trace_server_with_metrics_none(self, mock_credentials, mock_internet):
        """Test that tracing is skipped when enable_metrics is None."""
        mock_config = Mock()
        mock_config.enable_metrics = None
        mock_credentials.from_rc_file.return_value = mock_config
        mock_internet.return_value = True

        # Should not raise any errors
        trace_server_start_if_enabled()

        mock_credentials.from_rc_file.assert_called_once()

    @patch('guardrails_api.utils.trace_server_start_if_enabled.has_internet_connection')
    @patch('guardrails_api.utils.trace_server_start_if_enabled.Credentials')
    def test_loads_credentials_from_rc_file(self, mock_credentials, mock_internet):
        """Test that credentials are loaded from rc file."""
        mock_config = Mock()
        mock_config.enable_metrics = False
        mock_credentials.from_rc_file.return_value = mock_config

        trace_server_start_if_enabled()

        mock_credentials.from_rc_file.assert_called_once()


if __name__ == "__main__":
    unittest.main()
