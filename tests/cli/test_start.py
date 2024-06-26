from unittest.mock import MagicMock


def test_start(mocker):
    mocker.patch("guardrails_api.cli.start.cli")

    mock_flask_app = MagicMock()
    mock_create_app = mocker.patch(
        "guardrails_api.cli.start.create_app", return_value=mock_flask_app
    )

    from guardrails_api.cli.start import start

    start("env", "config", 8000)

    mock_create_app.assert_called_once_with("env", "config", 8000)
