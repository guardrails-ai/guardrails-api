def test_start(mocker):
    mocker.patch("guardrails_api.cli.start.cli")
    mock_gunicorn = mocker.patch("guardrails_api.cli.start.StandaloneApplication")

    mock_flask_app = mocker.stub()
    mock_create_app = mocker.patch(
        "guardrails_api.cli.start.create_app", return_value=mock_flask_app
    )

    from guardrails_api.cli.start import start

    start("env", "config")

    mock_gunicorn.assert_called_once_with(
        mock_flask_app,
        {
            "bind": "0.0.0.0:8000",
            "timeout": 5,
            "threads": 10,
        },
    )

    mock_create_app.assert_called_once_with("env", "config")
