from flask import Blueprint, request
from guardrails import Guard
from src.classes import GuardStruct, HttpError, ValidationOutput
from src.clients import GuardClient
from src.utils import (
    handle_error,
    get_llm_callable,
    cleanup_environment,
    prep_environment,
)

guards_bp = Blueprint("guards", __name__, url_prefix="/guards")


@guards_bp.route("/", methods=["GET", "POST"])
@handle_error
def guards():
    guard_client = GuardClient()
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
def guard(guard_name: str):
    guard_client = GuardClient()
    if request.method == "GET":
        as_of_query = request.args.get("asOf")
        guard = guard_client.get_guard(guard_name, as_of_query)
        return guard.to_response()
    elif request.method == "PUT":
        payload = request.json
        guard = GuardStruct.from_request(payload)
        updated_guard = guard_client.upsert_guard(guard_name, guard)
        return updated_guard.to_response()
    elif request.method == "DELETE":
        guard = guard_client.delete_guard(guard_name)
        return guard.to_response()
    else:
        raise HttpError(
            405,
            "Method Not Allowed",
            "/guard/<guard_name> only supports the GET, PUT, and DELETE methods."
            " You specified {request_method}".format(request_method=request.method),
        )


@guards_bp.route("/<guard_name>/validate", methods=["POST"])
@handle_error
def validate(guard_name: str):
    if request.method != "POST":
        raise HttpError(
            405,
            "Method Not Allowed",
            "/guards/<guard_name>/validate only supports the POST method. You specified"
            " {request_method}".format(request_method=request.method),
        )
    payload = request.json
    openai_api_key = request.headers.get("x-openai-api-key", None)
    guard_client = GuardClient()
    guard_struct = guard_client.get_guard(guard_name)
    prep_environment(guard_struct)
    guard: Guard = guard_struct.to_guard(openai_api_key)

    llm_output = payload.pop("llmOutput", None)
    num_reasks = payload.pop("numReasks", guard_struct.num_reasks)
    prompt_params = payload.pop("promptParams", None)
    llm_api = payload.pop("llmApi", None)
    args = payload.pop("args", [])

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

    # TODO: Get result from reduction of validator statuses when available
    result: bool = True
    validated_output: dict = None
    raw_llm_response: str = None

    if llm_output is not None:
        validated_output = guard.parse(
            llm_output=llm_output,
            num_reasks=num_reasks,
            prompt_params=prompt_params,
            llm_api=llm_api,
            *args,
            **payload
        )
    else:
        raw_llm_response, validated_output = guard(
            llm_api=llm_api,
            prompt_params=prompt_params,
            num_reasks=num_reasks,
            *args,
            **payload
        )

    cleanup_environment(guard_struct)
    return ValidationOutput(
        result, validated_output, guard.state.all_histories, raw_llm_response
    ).to_response()
