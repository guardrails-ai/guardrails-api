import os
import json
from flask import Blueprint, request
from urllib.parse import unquote_plus
from guardrails import Guard
from guardrails.utils.logs_utils import GuardLogs
from opentelemetry.trace import get_tracer
from src.classes.guard_struct import GuardStruct
from src.classes.http_error import HttpError
from src.classes.validation_output import ValidationOutput
from src.clients.guard_client import GuardClient
from src.utils.handle_error import handle_error
from src.utils.gather_request_metrics import gather_request_metrics
from src.utils.get_llm_callable import get_llm_callable
from src.utils.prep_environment import cleanup_environment, prep_environment


guards_bp = Blueprint("guards", __name__, url_prefix="/guards")
guard_client = GuardClient()


@guards_bp.route("/", methods=["GET", "POST"])
@handle_error
@gather_request_metrics
def guards():
    if request.method == "GET":
        guards = guard_client.get_guards()
        return [g.to_response() for g in guards]
    elif request.method == "POST":
        payload = request.json
        guard = GuardStruct.from_request(payload)
        new_guard = guard_client.create_guard(guard)
        return new_guard.to_response()
    else:
        raise HttpError(
            405,
            "Method Not Allowed",
            "/guards only supports the GET and POST methods. You specified"
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
        return guard.to_response()
    elif request.method == "PUT":
        payload = request.json
        guard = GuardStruct.from_request(payload)
        updated_guard = guard_client.upsert_guard(decoded_guard_name, guard)
        return updated_guard.to_response()
    elif request.method == "DELETE":
        guard = guard_client.delete_guard(decoded_guard_name)
        return guard.to_response()
    else:
        raise HttpError(
            405,
            "Method Not Allowed",
            "/guard/<guard_name> only supports the GET, PUT, and DELETE methods."
            " You specified {request_method}".format(
                request_method=request.method
            ),
        )


@guards_bp.route("/<guard_name>/validate", methods=["POST"])
@handle_error
@gather_request_metrics
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
    openai_api_key = request.headers.get("x-openai-api-key", None)
    decoded_guard_name = unquote_plus(guard_name)
    guard_struct = guard_client.get_guard(decoded_guard_name)
    prep_environment(guard_struct)

    llm_output = payload.pop("llmOutput", None)
    num_reasks = payload.pop("numReasks", guard_struct.num_reasks)
    prompt_params = payload.pop("promptParams", None)
    llm_api = payload.pop("llmApi", None)
    args = payload.pop("args", [])

    service_name = os.environ.get("OTEL_SERVICE_NAME", "guardrails-api")
    otel_tracer = get_tracer(service_name)

    with otel_tracer.start_as_current_span(
        f"validate-{decoded_guard_name}"
    ) as validate_span:
        guard: Guard = guard_struct.to_guard(openai_api_key, otel_tracer)

        validate_span.set_attribute("guardName", decoded_guard_name)
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

        result: bool = False
        validated_output: dict = None
        raw_llm_response: str = None

        if llm_output is not None:
            validated_output = guard.parse(
                llm_output=llm_output,
                num_reasks=num_reasks,
                prompt_params=prompt_params,
                llm_api=llm_api,
                *args,
                **payload,
            )
        else:
            raw_llm_response, validated_output = guard(
                llm_api=llm_api,
                prompt_params=prompt_params,
                num_reasks=num_reasks,
                *args,
                **payload,
            )

        guard_history = guard.state.most_recent_call
        last_step_logs: GuardLogs = guard_history.history[-1]
        validation_logs = last_step_logs.field_validation_logs.validator_logs
        failed_validations = list(
            [
                log
                for log in validation_logs
                if log.validation_result.outcome == "fail"
            ]
        )

        result = len(failed_validations) == 0
        raw_output = guard_history.output or raw_llm_response

        validation_output = ValidationOutput(
            result, validated_output, guard.state.all_histories, raw_output
        )

        prompt = (
            guard.rail.prompt.format(**(prompt_params or {})).source
            if guard.rail.prompt
            else None
        )
        if prompt:
            validate_span.set_attribute("prompt", prompt)

        instructions = (
            guard.rail.instructions.format(**(prompt_params or {})).source
            if guard.rail.instructions
            else None
        )
        if instructions:
            validate_span.set_attribute("instructions", instructions)

        validation_status = "pass" if result is True else "fail"
        validate_span.set_attribute("validation_status", validation_status)
        validate_span.set_attribute("raw_llm_ouput", raw_output)

        # Use the serialization from the class instead of re-writing it
        valid_output: str = (
            json.dumps(validation_output.validated_output)
            if isinstance(validation_output.validated_output, dict)
            else str(validation_output.validated_output)
        )
        validate_span.set_attribute("validated_output", valid_output)

        final_step_logs: GuardLogs = guard_history.history[-1]
        final_response = final_step_logs.llm_response
        prompt_token_count = final_response.prompt_token_count or 0
        response_token_count = final_response.response_token_count or 0
        total_token_count = prompt_token_count + response_token_count
        validate_span.set_attribute("tokens_consumed", total_token_count)

        num_of_reasks = (
            len(guard_history.history) - 1
            if len(guard_history.history) > 0
            else 0
        )
        validate_span.set_attribute("num_of_reasks", num_of_reasks)

    cleanup_environment(guard_struct)
    return validation_output.to_response()
