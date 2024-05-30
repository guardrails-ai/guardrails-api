from unittest.mock import PropertyMock, call
from typing import Dict, Tuple
from tests.mocks.mock_blueprint import MockBlueprint
from tests.mocks.mock_guard_client import MockGuardStruct
from tests.mocks.mock_request import MockRequest
from guardrails.classes import ValidationOutcome
from guardrails.classes.generic import Stack
from guardrails.classes.history import Call, CallInputs
from tests.mocks.mock_trace import MockTracer


def test_route_setup(mocker):
    mocker.patch("flask.Blueprint", new=MockBlueprint)

    from src.blueprints.guards import guards_bp

    assert guards_bp.route_call_count == 3
    assert guards_bp.routes == ["/", "/<guard_name>", "/<guard_name>/validate"]


def test_guards__get(mocker):
    mock_guard = MockGuardStruct()
    mock_request = MockRequest("GET")

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mock_get_guards = mocker.patch(
        "src.blueprints.guards.GuardClient.get_guards", return_value=[mock_guard]
    )
    mocker.patch("src.blueprints.guards.get_tracer")
    from src.blueprints.guards import guards

    response = guards()

    assert mock_get_guards.call_count == 1

    assert response == [{"name": "mock-guard"}]


def test_guards__post(mocker):
    mock_guard = MockGuardStruct()
    mock_request = MockRequest("POST", mock_guard.to_response())

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mock_from_request = mocker.patch(
        "src.blueprints.guards.GuardStruct.from_request", return_value=mock_guard
    )
    mock_create_guard = mocker.patch(
        "src.blueprints.guards.GuardClient.create_guard", return_value=mock_guard
    )
    mocker.patch("src.blueprints.guards.get_tracer")
    from src.blueprints.guards import guards

    response = guards()

    assert mock_from_request.called_once_with(mock_guard)
    assert mock_create_guard.called_once_with(mock_guard)

    assert response == {"name": "mock-guard"}


def test_guards__raises(mocker):
    mock_request = MockRequest("PUT")

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mocker.patch("src.blueprints.guards.get_tracer")
    mocker.patch("src.utils.handle_error.logger.error")
    mocker.patch("src.utils.handle_error.traceback.print_exception")
    from src.blueprints.guards import guards

    response = guards()

    assert isinstance(response, Tuple)
    error, status = response
    assert isinstance(error, Dict)
    assert error.get("status") == 405
    assert error.get("message") == "Method Not Allowed"
    assert (
        error.get("cause")
        == "/guards only supports the GET and POST methods. You specified PUT"
    )
    assert status == 405


def test_guard__get(mocker):
    mock_guard = MockGuardStruct()
    timestamp = "2024-03-04T14:11:42-06:00"
    mock_request = MockRequest("GET", args={"asOf": timestamp})

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "src.blueprints.guards.GuardClient.get_guard", return_value=mock_guard
    )
    mocker.patch("src.blueprints.guards.get_tracer")
    from src.blueprints.guards import guard

    response = guard("My%20Guard's%20Name")

    assert mock_get_guard.called_once_with("My Guard's Name", timestamp)
    assert response == {"name": "mock-guard"}


def test_guard__put(mocker):
    mock_guard = MockGuardStruct()
    mock_request = MockRequest("PUT", json={"name": "mock-guard"})

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mock_from_request = mocker.patch(
        "src.blueprints.guards.GuardStruct.from_request", return_value=mock_guard
    )
    mock_upsert_guard = mocker.patch(
        "src.blueprints.guards.GuardClient.upsert_guard", return_value=mock_guard
    )
    mocker.patch("src.blueprints.guards.get_tracer")
    from src.blueprints.guards import guard

    response = guard("My%20Guard's%20Name")

    assert mock_from_request.called_once_with(mock_guard)
    assert mock_upsert_guard.called_once_with("My Guard's Name", mock_guard)
    assert response == {"name": "mock-guard"}


def test_guard__delete(mocker):
    mock_guard = MockGuardStruct()
    mock_request = MockRequest("DELETE")

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mock_delete_guard = mocker.patch(
        "src.blueprints.guards.GuardClient.delete_guard", return_value=mock_guard
    )
    mocker.patch("src.blueprints.guards.get_tracer")
    from src.blueprints.guards import guard

    response = guard("my-guard-name")

    assert mock_delete_guard.called_once_with("my-guard-name")
    assert response == {"name": "mock-guard"}


def test_guard__raises(mocker):
    mock_request = MockRequest("POST")

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mocker.patch("src.blueprints.guards.get_tracer")
    mocker.patch("src.utils.handle_error.logger.error")
    mocker.patch("src.utils.handle_error.traceback.print_exception")
    from src.blueprints.guards import guard

    response = guard("guard")

    assert isinstance(response, Tuple)
    error, status = response
    assert isinstance(error, Dict)
    assert error.get("status") == 405
    assert error.get("message") == "Method Not Allowed"
    assert (
        error.get("cause")
        == "/guard/<guard_name> only supports the GET, PUT, and DELETE methods. You specified POST"
    )
    assert status == 405


def test_validate__raises_method_not_allowed(mocker):
    mock_request = MockRequest("PUT")

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mocker.patch("src.blueprints.guards.get_tracer")
    mocker.patch("src.utils.handle_error.logger.error")
    mocker.patch("src.utils.handle_error.traceback.print_exception")
    from src.blueprints.guards import validate

    response = validate("guard")

    assert isinstance(response, Tuple)
    error, status = response
    assert isinstance(error, Dict)
    assert error.get("status") == 405
    assert error.get("message") == "Method Not Allowed"
    assert (
        error.get("cause")
        == "/guards/<guard_name>/validate only supports the POST method. You specified PUT"
    )
    assert status == 405


def test_validate__raises_bad_request__openai_api_key(mocker):
    mock_guard = MockGuardStruct()
    mock_tracer = MockTracer()
    mock_request = MockRequest("POST", json={"llmApi": "bar"})

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "src.blueprints.guards.GuardClient.get_guard", return_value=mock_guard
    )
    mock_prep_environment = mocker.patch("src.blueprints.guards.prep_environment")
    mocker.patch("src.blueprints.guards.get_tracer", return_value=mock_tracer)
    mocker.patch("src.utils.handle_error.logger.error")
    mocker.patch("src.utils.handle_error.traceback.print_exception")
    from src.blueprints.guards import validate

    response = validate("My%20Guard's%20Name")

    assert mock_prep_environment.call_count == 1
    assert mock_get_guard.called_once_with("My Guard's Name")

    assert isinstance(response, Tuple)
    error, status = response
    assert isinstance(error, Dict)
    assert error.get("status") == 400
    assert error.get("message") == "BadRequest"
    assert error.get("cause") == (
        "Cannot perform calls to OpenAI without an api key.  Pass"
        " openai_api_key when initializing the Guard or set the"
        " OPENAI_API_KEY environment variable."
    )
    assert status == 400


def test_validate__raises_bad_request__num_reasks(mocker):
    mock_guard = MockGuardStruct()
    mock_tracer = MockTracer()
    mock_request = MockRequest("POST", json={"numReasks": 3})

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "src.blueprints.guards.GuardClient.get_guard", return_value=mock_guard
    )
    mock_prep_environment = mocker.patch("src.blueprints.guards.prep_environment")
    mocker.patch("src.blueprints.guards.get_tracer", return_value=mock_tracer)
    mocker.patch("src.utils.handle_error.logger.error")
    mocker.patch("src.utils.handle_error.traceback.print_exception")
    from src.blueprints.guards import validate

    response = validate("My%20Guard's%20Name")

    assert mock_prep_environment.call_count == 1
    assert mock_get_guard.called_once_with("My Guard's Name")

    assert isinstance(response, Tuple)
    error, status = response
    assert isinstance(error, Dict)
    assert error.get("status") == 400
    assert error.get("message") == "BadRequest"
    assert error.get("cause") == (
        "Cannot perform re-asks without an LLM API.  Specify llm_api when"
        " calling guard(...)."
    )
    assert status == 400


def test_validate__parse(mocker):
    mock_parse = mocker.patch.object(MockGuardStruct, "parse")
    mock_parse.return_value = ValidationOutcome(
        raw_llm_output="Hello world!",
        validated_output="Hello world!",
        validation_passed=True,
    )
    mock_guard = MockGuardStruct()
    mock_tracer = MockTracer()
    mock_request = MockRequest(
        "POST",
        json={"llmOutput": "Hello world!", "args": [1, 2, 3], "some_kwarg": "foo"},
    )

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "src.blueprints.guards.GuardClient.get_guard", return_value=mock_guard
    )
    mock_prep_environment = mocker.patch("src.blueprints.guards.prep_environment")
    mock_cleanup_environment = mocker.patch("src.blueprints.guards.cleanup_environment")
    mocker.patch("src.blueprints.guards.get_tracer", return_value=mock_tracer)

    set_attribute_spy = mocker.spy(mock_tracer.span, "set_attribute")

    mock_status = mocker.patch(
        "guardrails.classes.history.call.Call.status", new_callable=PropertyMock
    )
    mock_status.return_value = "pass"
    mock_guard.history = Stack(Call(inputs=CallInputs(prompt="Hello world prompt!")))
    from src.blueprints.guards import validate

    response = validate("My%20Guard's%20Name")

    assert mock_prep_environment.call_count == 1
    assert mock_get_guard.called_once_with("My Guard's Name")

    assert mock_parse.call_count == 1

    assert mock_parse.called_once_with(
        1,
        2,
        3,
        llm_output="Hello world!",
        num_reasks=0,
        prompt_params=None,
        llm_api=None,
        some_kwarg="foo",
    )

    assert set_attribute_spy.call_count == 7
    expected_calls = [
        call("guardName", "My Guard's Name"),
        call("prompt", "Hello world prompt!"),
        call("validation_status", "pass"),
        call("raw_llm_ouput", "Hello world!"),
        call("validated_output", "Hello world!"),
        call("tokens_consumed", None),
        call("num_of_reasks", 0),
    ]
    set_attribute_spy.assert_has_calls(expected_calls)

    assert mock_cleanup_environment.call_count == 1

    assert response == {
        "result": True,
        "validatedOutput": "Hello world!",
        "sessionHistory": [{"history": []}],
        "rawLlmResponse": "Hello world!",
    }


def test_validate__call(mocker):
    mock___call__ = mocker.patch.object(MockGuardStruct, "__call__")
    mock___call__.return_value = ValidationOutcome(
        raw_llm_output="Hello world!", validated_output=None, validation_passed=False
    )
    mock_guard = MockGuardStruct()
    mock_tracer = MockTracer()
    mock_request = MockRequest(
        "POST",
        json={
            "llmApi": "openai.Completion.create",
            "promptParams": {"p1": "bar"},
            "args": [1, 2, 3],
            "some_kwarg": "foo",
        },
        headers={"x-openai-api-key": "mock-key"},
    )

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("src.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "src.blueprints.guards.GuardClient.get_guard", return_value=mock_guard
    )
    mock_prep_environment = mocker.patch("src.blueprints.guards.prep_environment")
    mock_cleanup_environment = mocker.patch("src.blueprints.guards.cleanup_environment")
    mocker.patch("src.blueprints.guards.get_tracer", return_value=mock_tracer)

    set_attribute_spy = mocker.spy(mock_tracer.span, "set_attribute")

    mock_status = mocker.patch(
        "guardrails.classes.history.call.Call.status", new_callable=PropertyMock
    )
    mock_status.return_value = "fail"
    mock_guard.history = Stack(
        Call(
            inputs=CallInputs(
                prompt="Hello world prompt!", instructions="Hello world instructions!"
            )
        )
    )
    from src.blueprints.guards import validate

    response = validate("My%20Guard's%20Name")

    assert mock_prep_environment.call_count == 1
    assert mock_get_guard.called_once_with("My Guard's Name")

    assert mock___call__.call_count == 1

    assert mock___call__.called_once_with(
        1,
        2,
        3,
        llm_api="openai.Completion.create",
        prompt_params={"p1": "bar"},
        num_reasks=0,
        some_kwarg="foo",
    )

    assert set_attribute_spy.call_count == 8
    expected_calls = [
        call("guardName", "My Guard's Name"),
        call("prompt", "Hello world prompt!"),
        call("instructions", "Hello world instructions!"),
        call("validation_status", "fail"),
        call("raw_llm_ouput", "Hello world!"),
        call("validated_output", "None"),
        call("tokens_consumed", None),
        call("num_of_reasks", 0),
    ]
    set_attribute_spy.assert_has_calls(expected_calls)

    assert mock_cleanup_environment.call_count == 1

    assert response == {
        "result": False,
        "validatedOutput": None,
        "sessionHistory": [{"history": []}],
        "rawLlmResponse": "Hello world!",
    }
