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
from src.classes.guard_struct import GuardStruct
from src.classes.http_error import HttpError
from src.classes.validation_output import ValidationOutput
from src.clients.memory_guard_client import MemoryGuardClient
from src.clients.pg_guard_client import PGGuardClient
from src.utils.handle_error import handle_error
from src.utils.gather_request_metrics import gather_request_metrics
from src.utils.get_llm_callable import get_llm_callable
from src.utils.prep_environment import cleanup_environment, prep_environment


guards_bp = Blueprint("guards", __name__, url_prefix="/guards")

pg_host = os.environ.get("PGHOST", None)
# if no pg_host is set, use in memory guards
if pg_host is not None:
    guard_client = PGGuardClient()
else:
    guard_client = MemoryGuardClient()
    # read in guards from file
    import config
    exports = config.__dir__()
    for export_name in exports:
        export = getattr(config, export_name) 
        is_guard = isinstance(export, Guard)
        if is_guard:
            guard_client.create_guard(export)


@guards_bp.route("/", methods=["GET", "POST"])
@handle_error
@gather_request_metrics
def guards():
    if request.method == "GET":
        guards = guard_client.get_guards()
        if len(guards)>0 and (isinstance(guards[0], Guard)):
            return [g._to_request() for g in guards]
        return [g.to_response() for g in guards]
    elif request.method == "POST":
        raise HttpError(501, "Not Implemented", "POST /guards is not implemented.")
    else:
        raise HttpError(
            405,
            "Method Not Allowed",
            "/guards only supports the GET methods. You specified"
            " {request_method}".format(request_method=request.method),
        )


@guards_bp.route("/<guard_name>", methods=["GET", "PUT", "DELETE"])
@handle_error
@gather_request_metrics
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
        if isinstance(guard, Guard):
            return guard._to_request()
        return guard.to_response()
    elif request.method == "PUT":
        raise HttpError(501, "Not Implemented", "PUT /<guard_name> is not implemented.")
    elif request.method == "DELETE":
        raise HttpError(501, "Not Implemented", "DELETE /<guard_name> is not implemented.")
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
    validation_output: ValidationOutput,
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
@gather_request_metrics
def validate(guard_name: str):
    from rich import print

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
    openai_api_key = request.headers.get("x-openai-api-key", None)
    decoded_guard_name = unquote_plus(guard_name)
    guard_struct = guard_client.get_guard(decoded_guard_name)
    prep_environment(guard_struct)

    llm_output = payload.pop("llmOutput", None)
    num_reasks = payload.pop("numReasks", guard_struct.num_reasks)
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
    guard: Guard = guard_struct.to_guard(openai_api_key)

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
    elif num_reasks > 1:
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
            # api_key=openai_api_key,
            *args,
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
                    # api_key=openai_api_key,
                    *args,
                    **payload,
                )

                for result in guard_stream:
                    # TODO: Just make this a ValidationOutcome with history
                    validation_output: ValidationOutput = ValidationOutput(
                        result.validation_passed,
                        result.validated_output,
                        guard.history,
                        result.raw_llm_output,
                    )

                    yield validation_output, cast(ValidationOutcome, result)

            def validate_streamer(guard_iter):
                next_result = None
                # next_validation_output = None
                for validation_output, result in guard_iter:
                    next_result = result
                    # next_validation_output = validation_output
                    fragment = json.dumps(validation_output.to_response())
                    print("yielding fragment")
                    yield f"{fragment}\n"

                final_validation_output: ValidationOutput = ValidationOutput(
                    next_result.validation_passed,
                    next_result.validated_output,
                    guard.history,
                    next_result.raw_llm_output,
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
                final_output_json = json.dumps(final_validation_output.to_response())
                print("Yielding final output.")
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
    validation_output = ValidationOutput(
        result.validation_passed,
        result.validated_output,
        guard.history,
        result.raw_llm_output,
    )

    # collect_telemetry(
    #     guard=guard,
    #     validate_span=validate_span,
    #     validation_output=validation_output,
    #     prompt_params=prompt_params,
    #     result=result
    # )

    cleanup_environment(guard_struct)
    return validation_output.to_response()
