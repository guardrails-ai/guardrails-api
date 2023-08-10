from src.utils.logger import logger
from unittest.mock import MagicMock
from tests.mocks.mock_blueprint import MockBlueprint
from tests.mocks.mock_postgres_client import MockPostgresClient
from tests.mocks.mock_sql_alchemy import mock_text


def test_home(mocker):
    mocker.patch("flask.Blueprint", new=MockBlueprint)
    from src.blueprints.root import home, root_bp

    response = home()

    assert root_bp.route_call_count == 2
    assert root_bp.routes == ["/", "/health-check"]
    assert response == "Hello, Flask!"

    mocker.resetall()

def test_home(mocker):
    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("sqlalchemy.text", new=MagicMock(side_effect=mock_text))
    mock_pg = MockPostgresClient()
    mock_pg.db.session._set_rows([(1,)])
    class MockPg:
        def __init__(self):
          self.db = mock_pg.db
    mocker.patch("src.clients.postgres_client.PostgresClient", new=MockPg)
    info_spy = mocker.spy(logger, "info")
    from src.blueprints.root import health_check, root_bp, text, PostgresClient
    
    response = health_check()
    
    assert root_bp.name == "root"
    assert root_bp.routes == ["/", "/health-check"]
    text.assert_called_once_with("SELECT count(datid) FROM pg_stat_activity;")
    assert mock_pg.db.session.queries == ["SELECT count(datid) FROM pg_stat_activity;"]
    info_spy.assert_called_once_with("response: ", [(1,)])
    assert response == { "status": 200, "message": "Ok" }

    mocker.resetall()

