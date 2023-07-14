from pytest import MonkeyPatch
from tests.mocks.mock_blueprint import MockBlueprint

MonkeyPatch.setattr("flask", "Blueprint", MockBlueprint)

def test_home():
    from src.blueprints.root import home, root_bp
    response = home()
    assert response == "Hello, Flask!"
    assert root_bp.name == "root"
    assert root_bp.routes == ["/", "/health-check"]

