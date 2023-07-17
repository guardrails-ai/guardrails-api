import unittest
from unittest.mock import patch
from tests.mocks.mock_blueprint import MockBlueprint
from tests.mocks.mock_guard_client import MockGuardClient
from tests.mocks.mock_request import MockRequest
      
mock_request = MockRequest('GET')

class TestGuards(unittest.TestCase):
  
  @patch("flask.Blueprint", new=MockBlueprint)
  @patch("flask.request", mock_request)
  @patch("src.clients.guard_client.GuardClient", new=MockGuardClient)
  def test_guards_get(self):
      from src.blueprints.guards import guards, guards_bp, GuardClient

      print("GuardClient: ", GuardClient)

      # GuardClient.get_guards.return_value = 

      response = guards()

      assert guards_bp.route_call_count == 3
      assert guards_bp.routes == ["/", "/<guard_name>", "/<guard_name>/validate"]
      
      assert GuardClient.get_guards.call_count == 1

      assert response == "Hello, Flask!"

