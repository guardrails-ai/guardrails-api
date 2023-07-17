from unittest.mock import MagicMock
from tests.mocks.mock_blueprint import MockBlueprint
from tests.mocks.mock_guard_client import MockGuardClient
from tests.mocks.mock_request import MockRequest
from src.clients.guard_client import GuardClient
      

  
def test_guards_get(mocker):
    mock_request = MockRequest('GET')
    
    get_guards_spy = mocker.spy(MockGuardClient, 'get_guards')
    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("flask.request", mock_request)
    mocker.patch("src.clients.guard_client.GuardClient", new=MockGuardClient)
    from src.blueprints.guards import guards, guards_bp

    response = guards()

    assert guards_bp.route_call_count == 3
    assert guards_bp.routes == ["/", "/<guard_name>", "/<guard_name>/validate"]
    
    assert get_guards_spy.call_count == 1

    assert response == [{ "name": "mock-guard" }]

    mocker.resetall()

