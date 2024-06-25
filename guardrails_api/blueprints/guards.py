import json
import os
from guardrails.hub import *  # noqa
from string import Template
from typing import Any, Dict, cast
from flask import Blueprint, Response, request, stream_with_context
from urllib.parse import unquote_plus
from guardrails import Guard
from guardrails.classes import ValidationOutcome
from opentelemetry.trace import Span
from guardrails_api_client import Guard as GuardStruct
from guardrails_api.classes.http_error import HttpError
from guardrails_api.clients.cache_client import CacheClient
from guardrails_api.clients.memory_guard_client import MemoryGuardClient
from guardrails_api.clients.pg_guard_client import PGGuardClient
from guardrails_api.clients.postgres_client import postgres_is_enabled
from guardrails_api.utils.handle_error import handle_error
from guardrails_api.utils.get_llm_callable import get_llm_callable


guards_bp = Blueprint("guards", __name__, url_prefix="/guards")


# if no pg_host is set, use in memory guards
if postgres_is_enabled():
    guard_client = PGGuardClient()
else:
    guard_client = MemoryGuardClient()
    # Will be defined at runtime
    import config  # noqa

    exports = config.__dir__()
    for export_name in exports:
        export = getattr(config, export_name)
        is_guard = isinstance(export, Guard)
        if is_guard:
            guard_client.create_guard(export)

cache_client = CacheClient()


@guards_bp.route("/", methods=["GET", "POST"])
@handle_error
def guards():
    if request.method == "GET":
        guards = guard_client.get_guards()
        return [g.to_dict() for g in guards]
    elif request.method == "POST":
        if not postgres_is_enabled():
            raise HttpError(
                501,
                "NotImplemented",
                "POST /guards is not implemented for in-memory guards.",
            )
        payload = request.json
        guard = GuardStruct.from_dict(payload)
        new_guard = guard_client.create_guard(guard)
        return new_guard.to_dict()
    else:
        raise HttpError(
            405,
            "Method Not Allowed",
            "/guards only supports the GET and POST methods. You specified"
            " {request_method}".format(request_method=request.method),
        )


@guards_bp.route("/<guard_name>", methods=["GET", "PUT", "DELETE"])
@handle_error
def guard(guard_name: str):
    decoded_guard_name = unquote_plus(guard_name)
    if request.method == "GET":
        as_of_query = request.args.get("asOf")
        guard = guard_client.get_guard(decoded_guard_name, as_of_query)
        if guard is None:
            raise HttpError(
                404,
                "NotFound",
                "A Guard with the name {guard_name} does not exist!".format(
                    guard_name=decoded_guard_name
                ),
            )
        return guard.to_dict()
    elif request.method == "PUT":
        if not postgres_is_enabled():
            raise HttpError(
                501,
                "NotImplemented",
                "PUT /<guard_name> is not implemented for in-memory guards.",
            )
        payload = request.json
        guard = GuardStruct.from_dict(payload)
        updated_guard = guard_client.upsert_guard(decoded_guard_name, guard)
        return updated_guard.to_dict()
    elif request.method == "DELETE":
        if not postgres_is_enabled():
            raise HttpError(
                501,
                "NotImplemented",
                "DELETE /<guard_name> is not implemented for in-memory guards.",
            )
        guard = guard_client.delete_guard(decoded_guard_name)
        return guard.to_dict()
    else:
        raise HttpError(
            405,
            "Method Not Allowed",
            "/guard/<guard_name> only supports the GET, PUT, and DELETE methods."
            " You specified {request_method}".format(request_method=request.method),
        )


def collect_telemetry(
    *,
    guard: Guard,
    validate_span: Span,
    validation_output: ValidationOutcome,
    prompt_params: Dict[str, Any],
    result: ValidationOutcome,
):
    # Below is all telemetry collection and
    # should have no impact on what is returned to the user
    prompt = guard.history.last.inputs.prompt
    if prompt:
        prompt = Template(prompt).safe_substitute(**prompt_params)
        validate_span.set_attribute("prompt", prompt)

    instructions = guard.history.last.inputs.instructions
    if instructions:
        instructions = Template(instructions).safe_substitute(**prompt_params)
        validate_span.set_attribute("instructions", instructions)

    validate_span.set_attribute("validation_status", guard.history.last.status)
    validate_span.set_attribute("raw_llm_ouput", result.raw_llm_output)

    # Use the serialization from the class instead of re-writing it
    valid_output: str = (
        json.dumps(validation_output.validated_output)
        if isinstance(validation_output.validated_output, dict)
        else str(validation_output.validated_output)
    )
    validate_span.set_attribute("validated_output", valid_output)

    validate_span.set_attribute("tokens_consumed", guard.history.last.tokens_consumed)

    num_of_reasks = (
        guard.history.last.iterations.length - 1
        if guard.history.last.iterations.length > 0
        else 0
    )
    validate_span.set_attribute("num_of_reasks", num_of_reasks)


@guards_bp.route("/<guard_name>/validate", methods=["POST"])
@handle_error
def validate(guard_name: str):
    # Do we actually need a child span here?
    # We could probably use the existing span from the request unless we forsee
    #   capturing the same attributes on non-GaaS Guard runs.
    if request.method != "POST":
        raise HttpError(
            405,
            "Method Not Allowed",
            "/guards/<guard_name>/validate only supports the POST method. You specified"
            " {request_method}".format(request_method=request.method),
        )
    payload = request.json
    openai_api_key = request.headers.get(
        "x-openai-api-key", os.environ.get("OPENAI_API_KEY")
    )
    decoded_guard_name = unquote_plus(guard_name)
    guard_struct = guard_client.get_guard(decoded_guard_name)

    llm_output = payload.pop("llmOutput", None)
    num_reasks = payload.pop("numReasks", None)
    prompt_params = payload.pop("promptParams", {})
    llm_api = payload.pop("llmApi", None)
    args = payload.pop("args", [])
    stream = payload.pop("stream", False)

    # service_name = os.environ.get("OTEL_SERVICE_NAME", "guardrails-api")
    # otel_tracer = get_tracer(service_name)

    payload["api_key"] = payload.get("api_key", openai_api_key)

    # with otel_tracer.start_as_current_span(
    #     f"validate-{decoded_guard_name}"
    # ) as validate_span:
    # guard: Guard = guard_struct.to_guard(openai_api_key, otel_tracer)
    guard = guard_struct
    if not isinstance(guard_struct, Guard):
        guard: Guard = Guard.from_dict(guard_struct.to_dict())

    # validate_span.set_attribute("guardName", decoded_guard_name)
    if llm_api is not None:
        llm_api = get_llm_callable(llm_api)
        if openai_api_key is None:
            raise HttpError(
                status=400,
                message="BadRequest",
                cause=(
                    "Cannot perform calls to OpenAI without an api key.  Pass"
                    " openai_api_key when initializing the Guard or set the"
                    " OPENAI_API_KEY environment variable."
                ),
            )
    elif num_reasks and num_reasks > 1:
        raise HttpError(
            status=400,
            message="BadRequest",
            cause=(
                "Cannot perform re-asks without an LLM API.  Specify llm_api when"
                " calling guard(...)."
            ),
        )
    if llm_output is not None:
        if stream:
            raise HttpError(
                status=400,
                message="BadRequest",
                cause="Streaming is not supported for parse calls!",
            )
        result: ValidationOutcome = guard.parse(
            llm_output=llm_output,
            num_reasks=num_reasks,
            prompt_params=prompt_params,
            llm_api=llm_api,
            **payload,
        )
    else:
        if stream:

            def guard_streamer():
                guard_stream = guard(
                    llm_api=llm_api,
                    prompt_params=prompt_params,
                    num_reasks=num_reasks,
                    stream=stream,
                    *args,
                    **payload,
                )

                for result in guard_stream:
                    # TODO: Just make this a ValidationOutcome with history
                    validation_output: ValidationOutcome = (
                        ValidationOutcome.from_guard_history(guard.history.last)
                    )

                    # ValidationOutcome(
                    #     guard.history,
                    #     validation_passed=result.validation_passed,
                    #     validated_output=result.validated_output,
                    #     raw_llm_output=result.raw_llm_output,
                    # )
                    yield validation_output, cast(ValidationOutcome, result)

            def validate_streamer(guard_iter):
                next_result = None
                # next_validation_output = None
                for validation_output, result in guard_iter:
                    next_result = result
                    # next_validation_output = validation_output
                    fragment_dict = result.to_dict()
                    fragment_dict["error_spans"] = list(
                        map(
                            lambda x: json.dumps(
                                {"start": x.start, "end": x.end, "reason": x.reason}
                            ),
                            guard.error_spans_in_output(),
                        )
                    )
                    fragment = json.dumps(fragment_dict)
                    yield f"{fragment}\n"

                call = guard.history.last
                final_validation_output: ValidationOutcome = ValidationOutcome(
                    callId=call.id,
                    validation_passed=next_result.validation_passed,
                    validated_output=next_result.validated_output,
                    history=guard.history,
                    raw_llm_output=next_result.raw_llm_output,
                )
                # I don't know if these are actually making it to OpenSearch
                # because the span may be ended already
                # collect_telemetry(
                #     guard=guard,
                #     validate_span=validate_span,
                #     validation_output=next_validation_output,
                #     prompt_params=prompt_params,
                #     result=next_result
                # )
                final_output_dict = final_validation_output.to_dict()
                final_output_dict["error_spans"] = list(
                    map(
                        lambda x: json.dumps(
                            {"start": x.start, "end": x.end, "reason": x.reason}
                        ),
                        guard.error_spans_in_output(),
                    )
                )
                final_output_json = json.dumps(final_output_dict)
                yield f"{final_output_json}\n"

            return Response(
                stream_with_context(validate_streamer(guard_streamer())),
                content_type="application/json",
                # content_type="text/event-stream"
            )

        result: ValidationOutcome = guard(
            llm_api=llm_api,
            prompt_params=prompt_params,
            num_reasks=num_reasks,
            # api_key=openai_api_key,
            *args,
            **payload,
        )

    # TODO: Just make this a ValidationOutcome with history
    # validation_output = ValidationOutcome(
    #     validation_passed = result.validation_passed,
    #     validated_output=result.validated_output,
    #     history=guard.history,
    #     raw_llm_output=result.raw_llm_output,
    # )

    # collect_telemetry(
    #     guard=guard,
    #     validate_span=validate_span,
    #     validation_output=validation_output,
    #     prompt_params=prompt_params,
    #     result=result
    # )
    serialized_history = [call.to_dict() for call in guard.history]
    cache_key = f"{guard.name}-{result.call_id}"
    cache_client.set(cache_key, serialized_history, 300)
    return result.to_dict()


@guards_bp.route("/<guard_name>/history/<call_id>", methods=["GET"])
@handle_error
def guard_history(guard_name: str, call_id: str):
    if request.method == "GET":
        cache_key = f"{guard_name}-{call_id}"
        return cache_client.get(cache_key)
