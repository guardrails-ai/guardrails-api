from typer.testing import CliRunner

from guardrails_api.cli.db.db import db_command


class TestUpgrade:
    def test_default_revision_is_head(self, mocker):
        mock_upgrade_db = mocker.patch("guardrails_api.cli.db.upgrade.upgrade_db")
        mocker.patch("guardrails_api.cli.db.upgrade.os.path.isfile", return_value=False)

        runner = CliRunner()
        result = runner.invoke(db_command, ["upgrade"])

        assert result.exit_code == 0
        mock_upgrade_db.assert_called_once_with("head")

    def test_custom_revision(self, mocker):
        mock_upgrade_db = mocker.patch("guardrails_api.cli.db.upgrade.upgrade_db")
        mocker.patch("guardrails_api.cli.db.upgrade.os.path.isfile", return_value=False)

        runner = CliRunner()
        result = runner.invoke(db_command, ["upgrade", "abc123"])

        assert result.exit_code == 0
        mock_upgrade_db.assert_called_once_with("abc123")

    def test_loads_env_file_when_it_exists(self, mocker):
        mock_upgrade_db = mocker.patch("guardrails_api.cli.db.upgrade.upgrade_db")
        mocker.patch("guardrails_api.cli.db.upgrade.os.path.isfile", return_value=True)
        mock_load_dotenv = mocker.patch("guardrails_api.cli.db.upgrade.load_dotenv")

        runner = CliRunner()
        result = runner.invoke(db_command, ["upgrade"])

        assert result.exit_code == 0
        mock_load_dotenv.assert_called_once()
        mock_upgrade_db.assert_called_once_with("head")

    def test_does_not_load_env_file_when_it_does_not_exist(self, mocker):
        mock_upgrade_db = mocker.patch("guardrails_api.cli.db.upgrade.upgrade_db")
        mocker.patch("guardrails_api.cli.db.upgrade.os.path.isfile", return_value=False)
        mock_load_dotenv = mocker.patch("guardrails_api.cli.db.upgrade.load_dotenv")

        runner = CliRunner()
        result = runner.invoke(db_command, ["upgrade"])

        assert result.exit_code == 0
        mock_load_dotenv.assert_not_called()
        mock_upgrade_db.assert_called_once_with("head")

    def test_custom_env_file(self, mocker):
        mocker.patch("guardrails_api.cli.db.upgrade.upgrade_db")
        mocker.patch("guardrails_api.cli.db.upgrade.os.path.isfile", return_value=True)
        mock_load_dotenv = mocker.patch("guardrails_api.cli.db.upgrade.load_dotenv")

        runner = CliRunner()
        result = runner.invoke(db_command, ["upgrade", "--env", "/custom/.env"])

        assert result.exit_code == 0
        args, _ = mock_load_dotenv.call_args
        assert args[0] == "/custom/.env"

    def test_env_override_passed_to_load_dotenv(self, mocker):
        mock_upgrade_db = mocker.patch("guardrails_api.cli.db.upgrade.upgrade_db")
        mocker.patch("guardrails_api.cli.db.upgrade.os.path.isfile", return_value=True)
        mock_load_dotenv = mocker.patch("guardrails_api.cli.db.upgrade.load_dotenv")

        runner = CliRunner()
        result = runner.invoke(db_command, ["upgrade", "--env-override"])

        assert result.exit_code == 0
        _, kwargs = mock_load_dotenv.call_args
        assert kwargs.get("override") is True
        mock_upgrade_db.assert_called_once_with("head")

    def test_env_override_defaults_to_false(self, mocker):
        mocker.patch("guardrails_api.cli.db.upgrade.upgrade_db")
        mocker.patch("guardrails_api.cli.db.upgrade.os.path.isfile", return_value=True)
        mock_load_dotenv = mocker.patch("guardrails_api.cli.db.upgrade.load_dotenv")

        runner = CliRunner()
        result = runner.invoke(db_command, ["upgrade"])

        assert result.exit_code == 0
        _, kwargs = mock_load_dotenv.call_args
        assert kwargs.get("override") is False

    def test_all_options(self, mocker):
        mock_upgrade_db = mocker.patch("guardrails_api.cli.db.upgrade.upgrade_db")
        mocker.patch("guardrails_api.cli.db.upgrade.os.path.isfile", return_value=True)
        mock_load_dotenv = mocker.patch("guardrails_api.cli.db.upgrade.load_dotenv")

        runner = CliRunner()
        result = runner.invoke(
            db_command,
            ["upgrade", "v2", "--env", "prod.env", "--env-override"],
        )

        assert result.exit_code == 0
        args, kwargs = mock_load_dotenv.call_args
        assert args[0] == "prod.env"
        assert kwargs.get("override") is True
        mock_upgrade_db.assert_called_once_with("v2")
