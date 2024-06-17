import os
from guardrails_api.utils.logger import logger
from tests.mocks.mock_blueprint import MockBlueprint
from tests.mocks.mock_postgres_client import MockPostgresClient


def test_home(mocker):
    mocker.patch("flask.Blueprint", new=MockBlueprint)
    from guardrails_api.blueprints.root import home, root_bp

    response = home()

    assert root_bp.route_call_count == 4
    assert root_bp.routes == ["/", "/health-check", "/api-docs", "/docs"]
    assert response == "Hello, Flask!"

    mocker.resetall()


def test_health_check(mocker):
    os.environ["PGHOST"] = "localhost"
    mocker.patch("flask.Blueprint", new=MockBlueprint)

    mock_pg = MockPostgresClient()
    mock_pg.db.session._set_rows([(1,)])
    mocker.patch("guardrails_api.blueprints.root.PostgresClient", return_value=mock_pg)

    def text_side_effect(query: str):
        return query

    mock_text = mocker.patch(
        "guardrails_api.blueprints.root.text", side_effect=text_side_effect
    )

    from guardrails_api.blueprints.root import health_check

    info_spy = mocker.spy(logger, "info")

    response = health_check()

    mock_text.assert_called_once_with("SELECT count(datid) FROM pg_stat_activity;")
    assert mock_pg.db.session.queries == ["SELECT count(datid) FROM pg_stat_activity;"]

    info_spy.assert_called_once_with("response: %s", [(1,)])
    assert response == {"status": 200, "message": "Ok"}

    mocker.resetall()
    del os.environ["PGHOST"]
