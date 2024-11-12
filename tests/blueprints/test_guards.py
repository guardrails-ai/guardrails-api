import os
from unittest.mock import PropertyMock
from typing import Dict, Tuple

import pytest

from tests.mocks.mock_blueprint import MockBlueprint
from tests.mocks.mock_guard_client import MockGuardStruct
from tests.mocks.mock_request import MockRequest
from guardrails.classes import ValidationOutcome
from guardrails.classes.generic import Stack
from guardrails.classes.history import Call, Iteration
from guardrails_api.app import register_config
from guardrails.errors import ValidationError

# TODO: Should we mock this somehow?
#   Right now it's just empty, but it technically does a file read
register_config()


MOCK_GUARD_STRING = {
    "id": "mock-guard-id",
    "name": "mock-guard",
    "description": "mock guard description",
    "history": Stack(),
}


# FIXME: Why doesn't this work when running a single test?
# Either a config issue or a pytest issue
@pytest.fixture(autouse=True)
def around_each():
    # Code that will run before the test
    openai_api_key_bak = os.environ.get("OPENAI_API_KEY")
    if openai_api_key_bak:
        del os.environ["OPENAI_API_KEY"]
    yield
    # Code that will run after the test
    if openai_api_key_bak:
        os.environ["OPENAI_API_KEY"] = openai_api_key_bak


def test_route_setup(mocker):
    mocker.patch("flask.Blueprint", new=MockBlueprint)

    from guardrails_api.blueprints.guards import guards_bp

    assert guards_bp.route_call_count == 5
    assert guards_bp.routes == [
        "/",
        "/<guard_name>",
        "/<guard_name>/openai/v1/chat/completions",
        "/<guard_name>/validate",
        "/<guard_name>/history/<call_id>",
    ]


def test_guards__get(mocker):
    mock_guard = MockGuardStruct()
    mock_request = MockRequest("GET")

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    mock_get_guards = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.get_guards",
        return_value=[mock_guard],
    )
    mocker.patch("guardrails_api.blueprints.guards.collect_telemetry")

    # >>> Conflict
    # mock_get_guards = mocker.patch(
    #     "guardrails_api.blueprints.guards.guard_client.get_guards", return_value=[mock_guard]
    # )
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer")

    from guardrails_api.blueprints.guards import guards

    response = guards()

    assert mock_get_guards.call_count == 1

    assert response == [MOCK_GUARD_STRING]


def test_guards__post_pg(mocker):
    os.environ["PGHOST"] = "localhost"
    mock_guard = MockGuardStruct()
    mock_request = MockRequest("POST", mock_guard.to_dict())

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    mock_from_request = mocker.patch(
        "guardrails_api.blueprints.guards.GuardStruct.from_dict",
        return_value=mock_guard,
    )
    mock_create_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.create_guard",
        return_value=mock_guard,
    )

    from guardrails_api.blueprints.guards import guards

    response = guards()

    mock_from_request.assert_called_once_with(mock_guard.to_dict())
    mock_create_guard.assert_called_once_with(mock_guard)

    assert response == MOCK_GUARD_STRING

    del os.environ["PGHOST"]


def test_guards__post_mem(mocker):
    mock_guard = MockGuardStruct()
    mock_request = MockRequest("POST", mock_guard.to_dict())

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)

    from guardrails_api.blueprints.guards import guards

    response = guards()

    error_body, status = response

    assert status == 501


def test_guards__raises(mocker):
    mock_request = MockRequest("PUT")

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer")
    mocker.patch("guardrails_api.utils.handle_error.logger.error")
    mocker.patch("guardrails_api.utils.handle_error.traceback.print_exception")
    from guardrails_api.blueprints.guards import guards

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


def test_guard__get_mem(mocker):
    mock_guard = MockGuardStruct()
    timestamp = "2024-03-04T14:11:42-06:00"
    mock_request = MockRequest("GET", args={"asOf": timestamp})

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)

    mock_get_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.get_guard",
        return_value=mock_guard,
    )
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer")

    # >>> Conflict
    # mock_get_guard = mocker.patch(
    #     "guardrails_api.blueprints.guards.guard_client.get_guard", return_value=mock_guard
    # )
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer")

    from guardrails_api.blueprints.guards import guard

    response = guard("My%20Guard's%20Name")

    mock_get_guard.assert_called_once_with("My Guard's Name", timestamp)
    assert response == MOCK_GUARD_STRING


def test_guard__put_pg(mocker):
    os.environ["PGHOST"] = "localhost"
    mock_guard = MockGuardStruct()
    json_guard = {
        "name": "mock-guard",
        "id": "mock-guard-id",
        "description": "mock guard description",
        "history": Stack(),
    }
    mock_request = MockRequest("PUT", json=json_guard)

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)

    mock_from_request = mocker.patch(
        "guardrails_api.blueprints.guards.GuardStruct.from_dict",
        return_value=mock_guard,
    )
    mock_upsert_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.upsert_guard",
        return_value=mock_guard,
    )
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer")

    # >>> Conflict
    # mock_from_request = mocker.patch(
    #     "guardrails_api.blueprints.guards.GuardStruct.from_request", return_value=mock_guard
    # )
    # mock_upsert_guard = mocker.patch(
    #     "guardrails_api.blueprints.guards.guard_client.upsert_guard", return_value=mock_guard
    # )
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer")

    from guardrails_api.blueprints.guards import guard

    response = guard("My%20Guard's%20Name")

    mock_from_request.assert_called_once_with(json_guard)
    mock_upsert_guard.assert_called_once_with("My Guard's Name", mock_guard)
    assert response == MOCK_GUARD_STRING
    del os.environ["PGHOST"]


def test_guard__delete_pg(mocker):
    os.environ["PGHOST"] = "localhost"
    mock_guard = MockGuardStruct()
    mock_request = MockRequest("DELETE")

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)

    mock_delete_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.delete_guard",
        return_value=mock_guard,
    )
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer")

    # >>> Conflict
    # mock_delete_guard = mocker.patch(
    #     "guardrails_api.blueprints.guards.guard_client.delete_guard", return_value=mock_guard
    # )
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer")

    from guardrails_api.blueprints.guards import guard

    response = guard("my-guard-name")

    mock_delete_guard.assert_called_once_with("my-guard-name")
    assert response == MOCK_GUARD_STRING
    del os.environ["PGHOST"]


def test_guard__raises(mocker):
    mock_request = MockRequest("POST")

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer")
    mocker.patch("guardrails_api.utils.handle_error.logger.error")
    mocker.patch("guardrails_api.utils.handle_error.traceback.print_exception")
    from guardrails_api.blueprints.guards import guard

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
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer")
    mocker.patch("guardrails_api.utils.handle_error.logger.error")
    mocker.patch("guardrails_api.utils.handle_error.traceback.print_exception")
    from guardrails_api.blueprints.guards import validate

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
    os.environ["PGHOST"] = "localhost"
    mock_guard = MockGuardStruct()
    # mock_tracer = MockTracer()
    mock_request = MockRequest("POST", json={"llmApi": "bar"})

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.get_guard",
        return_value=mock_guard,
    )

    # mocker.patch("guardrails_api.blueprints.guards.get_tracer", return_value=mock_tracer)
    mocker.patch("guardrails_api.utils.handle_error.logger.error")
    mocker.patch("guardrails_api.utils.handle_error.traceback.print_exception")
    from guardrails_api.blueprints.guards import validate

    response = validate("mock-guard")

    mock_get_guard.assert_called_once_with("mock-guard")

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
    del os.environ["PGHOST"]


def test_validate__raises_bad_request__num_reasks(mocker):
    os.environ["PGHOST"] = "localhost"
    mock_guard = MockGuardStruct()
    # mock_tracer = MockTracer()
    mock_request = MockRequest("POST", json={"numReasks": 3})

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.get_guard",
        return_value=mock_guard,
    )
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer", return_value=mock_tracer)
    mocker.patch("guardrails_api.utils.handle_error.logger.error")
    mocker.patch("guardrails_api.utils.handle_error.traceback.print_exception")
    from guardrails_api.blueprints.guards import validate

    response = validate("mock-guard")

    mock_get_guard.assert_called_once_with("mock-guard")

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
    del os.environ["PGHOST"]


def test_validate__parse(mocker):
    os.environ["PGHOST"] = "localhost"
    mock_outcome = ValidationOutcome(
        call_id="mock-call-id",
        raw_llm_output="Hello world!",
        validated_output="Hello world!",
        validation_passed=True,
    )

    mock_parse = mocker.patch.object(MockGuardStruct, "parse")
    mock_parse.return_value = mock_outcome

    mock_guard = MockGuardStruct()
    mock_from_dict = mocker.patch("guardrails_api.blueprints.guards.Guard.from_dict")
    mock_from_dict.return_value = mock_guard

    # mock_tracer = MockTracer()
    mock_request = MockRequest(
        "POST",
        json={"llmOutput": "Hello world!", "args": [1, 2, 3], "some_kwarg": "foo"},
    )

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.get_guard",
        return_value=mock_guard,
    )

    mocker.patch("guardrails_api.blueprints.guards.CacheClient.set")

    # mocker.patch("guardrails_api.blueprints.guards.get_tracer", return_value=mock_tracer)

    # >>> Conflict
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer", return_value=mock_tracer)

    # set_attribute_spy = mocker.spy(mock_tracer.span, "set_attribute")

    mock_status = mocker.patch(
        "guardrails.classes.history.call.Call.status", new_callable=PropertyMock
    )
    mock_status.return_value = "pass"
    mock_guard.history = Stack(Call())
    from guardrails_api.blueprints.guards import validate

    response = validate("My%20Guard's%20Name")

    mock_get_guard.assert_called_once_with("My Guard's Name")

    assert mock_parse.call_count == 1

    mock_parse.assert_called_once_with(
        llm_output="Hello world!",
        num_reasks=None,
        prompt_params={},
        llm_api=None,
        some_kwarg="foo",
        api_key=None,
    )

    # Temporarily Disabled
    # assert set_attribute_spy.call_count == 7
    # expected_calls = [
    #     call("guardName", "My Guard's Name"),
    #     call("prompt", "Hello world prompt!"),
    #     call("validation_status", "pass"),
    #     call("raw_llm_ouput", "Hello world!"),
    #     call("validated_output", "Hello world!"),
    #     call("tokens_consumed", None),
    #     call("num_of_reasks", 0),
    # ]
    # set_attribute_spy.assert_has_calls(expected_calls)

    assert response == {
        "callId": "mock-call-id",
        "validatedOutput": "Hello world!",
        "validationPassed": True,
        "rawLlmOutput": "Hello world!",
    }

    del os.environ["PGHOST"]


def test_validate__call(mocker):
    os.environ["PGHOST"] = "localhost"
    mock_guard = MockGuardStruct()
    mock_outcome = ValidationOutcome(
        call_id="mock-call-id",
        raw_llm_output="Hello world!",
        validated_output=None,
        validation_passed=False,
    )

    mock___call__ = mocker.patch.object(MockGuardStruct, "__call__")
    mock___call__.return_value = mock_outcome

    mock_guard = MockGuardStruct()
    mock_from_dict = mocker.patch("guardrails_api.blueprints.guards.Guard.from_dict")
    mock_from_dict.return_value = mock_guard

    # mock_tracer = MockTracer()
    mock_request = MockRequest(
        "POST",
        json={
            "llmApi": "openai.Completion.create",
            "promptParams": {"p1": "bar"},
            "args": [1, 2, 3],
            "some_kwarg": "foo",
            "prompt": "Hello world!",
        },
        headers={"x-openai-api-key": "mock-key"},
    )

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.get_guard",
        return_value=mock_guard,
    )
    mocker.patch(
        "guardrails_api.blueprints.guards.get_llm_callable",
        return_value="openai.Completion.create",
    )

    mocker.patch("guardrails_api.blueprints.guards.CacheClient.set")

    # mocker.patch("guardrails_api.blueprints.guards.get_tracer", return_value=mock_tracer)

    # >>> Conflict
    # mocker.patch("guardrails_api.blueprints.guards.get_tracer", return_value=mock_tracer)

    # set_attribute_spy = mocker.spy(mock_tracer.span, "set_attribute")

    mock_status = mocker.patch(
        "guardrails.classes.history.call.Call.status", new_callable=PropertyMock
    )
    mock_status.return_value = "fail"
    mock_guard.history = Stack(Call())
    from guardrails_api.blueprints.guards import validate

    response = validate("My%20Guard's%20Name")

    mock_get_guard.assert_called_once_with("My Guard's Name")

    assert mock___call__.call_count == 1

    mock___call__.assert_called_once_with(
        1,
        2,
        3,
        llm_api="openai.Completion.create",
        prompt_params={"p1": "bar"},
        num_reasks=None,
        some_kwarg="foo",
        api_key="mock-key",
        prompt="Hello world!",
    )

    # Temporarily Disabled
    # assert set_attribute_spy.call_count == 8
    # expected_calls = [
    #     call("guardName", "My Guard's Name"),
    #     call("prompt", "Hello world prompt!"),
    #     call("instructions", "Hello world instructions!"),
    #     call("validation_status", "fail"),
    #     call("raw_llm_ouput", "Hello world!"),
    #     call("validated_output", "None"),
    #     call("tokens_consumed", None),
    #     call("num_of_reasks", 0),
    # ]
    # set_attribute_spy.assert_has_calls(expected_calls)

    assert response == {
        "callId": "mock-call-id",
        "validationPassed": False,
        "validatedOutput": None,
        "rawLlmOutput": "Hello world!",
    }

    del os.environ["PGHOST"]


def test_validate__call_throws_validation_error(mocker):
    os.environ["PGHOST"] = "localhost"

    mock___call__ = mocker.patch.object(MockGuardStruct, "__call__")
    mock___call__.side_effect = ValidationError("Test guard validation error")

    mock_guard = MockGuardStruct()
    mock_from_dict = mocker.patch("guardrails_api.blueprints.guards.Guard.from_dict")
    mock_from_dict.return_value = mock_guard

    # mock_tracer = MockTracer()
    mock_request = MockRequest(
        "POST",
        json={
            "llmApi": "openai.Completion.create",
            "promptParams": {"p1": "bar"},
            "args": [1, 2, 3],
            "some_kwarg": "foo",
            "prompt": "Hello world!",
        },
        headers={"x-openai-api-key": "mock-key"},
    )

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.get_guard",
        return_value=mock_guard,
    )
    mocker.patch(
        "guardrails_api.blueprints.guards.get_llm_callable",
        return_value="openai.Completion.create",
    )

    mocker.patch("guardrails_api.blueprints.guards.CacheClient.set")

    mock_status = mocker.patch(
        "guardrails.classes.history.call.Call.status", new_callable=PropertyMock
    )
    mock_status.return_value = "fail"
    mock_guard.history = Stack(Call())
    from guardrails_api.blueprints.guards import validate

    response = validate("My%20Guard's%20Name")

    mock_get_guard.assert_called_once_with("My Guard's Name")

    assert mock___call__.call_count == 1

    mock___call__.assert_called_once_with(
        1,
        2,
        3,
        llm_api="openai.Completion.create",
        prompt_params={"p1": "bar"},
        num_reasks=None,
        some_kwarg="foo",
        api_key="mock-key",
        prompt="Hello world!",
    )

    assert response == (
        {"status_code": 400, "detail": "Test guard validation error"},
        400,
    )

    del os.environ["PGHOST"]


def test_openai_v1_chat_completions__raises_404(mocker):
    from guardrails_api.blueprints.guards import openai_v1_chat_completions

    os.environ["PGHOST"] = "localhost"
    mock_guard = None

    mock_request = MockRequest(
        "POST",
        json={
            "messages": [{"role": "user", "content": "Hello world!"}],
        },
        headers={"x-openai-api-key": "mock-key"},
    )

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.get_guard",
        return_value=mock_guard,
    )
    mocker.patch("guardrails_api.blueprints.guards.CacheClient.set")

    response = openai_v1_chat_completions("My%20Guard's%20Name")
    assert response[1] == 404
    assert response[0]["message"] == "NotFound"

    mock_get_guard.assert_called_once_with("My Guard's Name")

    del os.environ["PGHOST"]


def test_openai_v1_chat_completions__call(mocker):
    from guardrails_api.blueprints.guards import openai_v1_chat_completions

    os.environ["PGHOST"] = "localhost"
    mock_guard = MockGuardStruct()
    mock_outcome = ValidationOutcome(
        call_id="mock-call-id",
        raw_llm_output="Hello world!",
        validated_output="Hello world!",
        validation_passed=False,
    )

    mock___call__ = mocker.patch.object(MockGuardStruct, "__call__")
    mock___call__.return_value = mock_outcome

    mock_from_dict = mocker.patch("guardrails_api.blueprints.guards.Guard.from_dict")
    mock_from_dict.return_value = mock_guard

    mock_request = MockRequest(
        "POST",
        json={
            "messages": [{"role": "user", "content": "Hello world!"}],
        },
        headers={"x-openai-api-key": "mock-key"},
    )

    mocker.patch("flask.Blueprint", new=MockBlueprint)
    mocker.patch("guardrails_api.blueprints.guards.request", mock_request)
    mock_get_guard = mocker.patch(
        "guardrails_api.blueprints.guards.guard_client.get_guard",
        return_value=mock_guard,
    )
    mocker.patch(
        "guardrails_api.blueprints.guards.get_llm_callable",
        return_value="openai.Completion.create",
    )

    mocker.patch("guardrails_api.blueprints.guards.CacheClient.set")

    mock_status = mocker.patch(
        "guardrails.classes.history.call.Call.status", new_callable=PropertyMock
    )
    mock_status.return_value = "fail"
    mock_call = Call()
    mock_call.iterations = Stack(Iteration("some-id", 1))
    mock_guard.history = Stack(mock_call)

    response = openai_v1_chat_completions("My%20Guard's%20Name")

    mock_get_guard.assert_called_once_with("My Guard's Name")

    assert mock___call__.call_count == 1

    mock___call__.assert_called_once_with(
        num_reasks=0,
        messages=[{"role": "user", "content": "Hello world!"}],
    )

    assert response == {
        "choices": [
            {
                "message": {
                    "content": "Hello world!",
                },
            }
        ],
        "guardrails": {
            "reask": None,
            "validation_passed": False,
            "error": None,
        },
    }

    del os.environ["PGHOST"]
