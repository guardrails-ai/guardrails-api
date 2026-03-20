import json
import os
import inspect
from typing import Any, Optional
import warnings
from fastapi import HTTPException, Request, APIRouter
from fastapi.responses import StreamingResponse
from urllib.parse import unquote_plus
from guardrails import AsyncGuard, Guard
from guardrails.classes import ValidationOutcome
from guardrails.classes.history import Call
from guardrails_api.classes.create_chat_completion_request import (
    CreateChatCompletionRequest,
)
from guardrails_api.classes.guarded_chat_completion import GuardedChatCompletion
from guardrails_api.clients.get_guard_client import get_guard_client
from guardrails_api.clients.cache_client import CacheClient
from guardrails_api.db.postgres_client import postgres_is_enabled
from guardrails_api.utils.attach_validation_summaries import attach_validation_summaries
from guardrails_api.utils.openai import (
    guarded_chat_completion,
    guarded_chat_completion_stream,
)
from guardrails_api.utils.handle_error import handle_error
from guardrails_api.classes.http_error import HttpError
from guardrails_ai.types import Guard as IGuard, CreateGuardRequest
from guardrails_api.classes.validate_request import ValidateRequest

cache_client = CacheClient()

cache_client.initialize()

router = APIRouter()


def guard_history_is_enabled():
    return os.environ.get("GUARD_HISTORY_ENABLED", "true").lower() == "true"


def to_IGuard(guard: Guard | AsyncGuard | IGuard) -> IGuard:
    return (
        IGuard.model_validate(guard.model_dump(exclude_none=True))
        if isinstance(guard, Guard)
        else guard
    )


@router.get("/guards")
@handle_error
async def get_guards(name: Optional[str] = None) -> list[IGuard]:
    guard_client = get_guard_client()
    guard_name = unquote_plus(name) if name else None
    guards = guard_client.get_guards(guard_name=guard_name)
    return [to_IGuard(g) for g in guards]


@router.post("/guards")
@handle_error
async def create_guard(guard: CreateGuardRequest) -> IGuard:
    guard_client = get_guard_client()
    if not postgres_is_enabled():
        raise HTTPException(
            status_code=501,
            detail="Not Implemented POST /guards is not implemented for in-memory guards.",
        )

    new_guard = guard_client.create_guard(guard)  # type: ignore
    return new_guard


@router.get("/guards/{id}")
@handle_error
async def get_guard(id: str, asOf: Optional[str] = None) -> IGuard:
    guard_client = get_guard_client()
    decoded_guard_id = unquote_plus(id)
    guard = guard_client.get_guard(decoded_guard_id, asOf)
    if guard is None:
        raise HTTPException(
            status_code=404,
            detail=f"A Guard with the id {decoded_guard_id} does not exist!",
        )
    return to_IGuard(guard)


@router.put("/guards/{id}")
@handle_error
async def update_guard(id: str, guard: IGuard) -> IGuard:
    guard_client = get_guard_client()
    if not postgres_is_enabled():
        raise HTTPException(
            status_code=501,
            detail="PUT /guards/{id} is not implemented for in-memory guards.",
        )

    decoded_guard_id = unquote_plus(id)
    updated_guard = guard_client.upsert_guard(decoded_guard_id, guard)  # type: ignore
    return updated_guard


@router.delete("/guards/{id}")
@handle_error
async def delete_guard(id: str) -> IGuard:
    guard_client = get_guard_client()
    if not postgres_is_enabled():
        raise HTTPException(
            status_code=501,
            detail="DELETE /guards/{id} is not implemented for in-memory guards.",
        )
    decoded_guard_id = unquote_plus(id)
    guard = guard_client.delete_guard(decoded_guard_id)
    return guard


@router.post(
    "/guards/{id}/openai/v1/chat/completions",
    response_model=None,  # Disable default to allow Union/Direct Response
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "schema": GuardedChatCompletion.model_json_schema()
                },
                "text/event-stream": {"additionalProperties": True},
            },
        }
    },
)
@handle_error
async def openai_v1_chat_completions(
    id: str, create_chat_completion_request: CreateChatCompletionRequest
) -> GuardedChatCompletion | StreamingResponse:
    payload = dict(create_chat_completion_request)
    guard_client = get_guard_client()
    decoded_guard_id = unquote_plus(id)
    guard_struct = guard_client.get_guard(decoded_guard_id)
    if guard_struct is None:
        raise HTTPException(
            status_code=404,
            detail=f"A Guard with the id {decoded_guard_id} does not exist!",
        )

    guard = (
        AsyncGuard.from_dict(guard_struct.model_dump(exclude_none=True))
        if not isinstance(guard_struct, Guard)
        else guard_struct
    )
    if not guard:
        raise HttpError(
            status=404, message=f"Guard with id {decoded_guard_id} not found!"
        )
    stream = payload.get("stream", False)

    if not stream:
        guarded_completion = await guarded_chat_completion(guard, payload)
        return guarded_completion
    else:
        guarded_completion_stream = await guarded_chat_completion_stream(guard, payload)
        return StreamingResponse(
            guarded_completion_stream, media_type="text/event-stream"
        )


@router.post(
    "/guards/{id}/validate",
    response_model=None,  # Disable default to allow Union/Direct Response
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {"schema": ValidationOutcome.model_json_schema()},
                "text/event-stream": {"additionalProperties": True},
            },
        }
    },
)
@handle_error
async def validate(
    id: str, validate_request: ValidateRequest, request: Request
) -> ValidationOutcome | StreamingResponse:
    guard_client = get_guard_client()
    payload: dict[str, Any] = {**validate_request}
    openai_api_key = request.headers.get(
        "x-openai-api-key", os.environ.get("OPENAI_API_KEY")
    )
    decoded_guard_id = unquote_plus(id)
    guard_struct = guard_client.get_guard(decoded_guard_id)

    llm_output = payload.pop("llm_output", None)
    num_reasks = payload.pop("num_reasks", None)
    prompt_params = payload.pop("prompt_params", {})
    _llm_api = payload.pop("llm_api", None)
    if _llm_api:
        warnings.warn(
            "Specifying llmApi is deprecated.  Its value will be ignored.",
            DeprecationWarning,
        )
    args = payload.pop("args", [])
    stream = payload.pop("stream", False)

    payload["api_key"] = payload.get("api_key", openai_api_key)

    guard: Guard | AsyncGuard | None
    if isinstance(guard_struct, IGuard):
        guard = AsyncGuard.from_dict(guard_struct.model_dump(exclude_none=True))
    else:
        guard = guard_struct

    if not guard:
        raise HttpError(
            status=404,
            message="NotFound",
            cause="A Guard with the id {id} does not exist!".format(id=id),
        )

    if llm_output is not None:
        if stream:
            raise HTTPException(
                status_code=400, detail="Streaming is not supported for parse calls!"
            )
        execution = guard.parse(
            llm_output=llm_output,
            num_reasks=num_reasks,
            prompt_params=prompt_params,
            **payload,
        )
        if inspect.iscoroutine(execution):
            result: ValidationOutcome = await execution  # type: ignore - AsyncGuard.parse returns Awaitable[ValidationOutcome] when it doesn't need to
        else:
            result: ValidationOutcome = execution
    else:
        if stream:

            async def guard_streamer():
                call = guard(
                    prompt_params=prompt_params,
                    num_reasks=num_reasks,
                    stream=stream,
                    *args,
                    **payload,
                )
                is_async = inspect.iscoroutine(call)
                if is_async:
                    guard_stream = await call
                    async for result in guard_stream:
                        validation_output = ValidationOutcome.from_guard_history(
                            guard.history.last
                        )
                        yield validation_output, result
                else:
                    guard_stream = call
                    for result in guard_stream:
                        validation_output = ValidationOutcome.from_guard_history(
                            guard.history.last
                        )
                        yield validation_output, result

            async def validate_streamer(guard_iter):
                try:
                    async for validation_output, result in guard_iter:
                        fragment_dict = result.to_dict()
                        fragment_dict["error_spans"] = [
                            json.dumps(
                                {"start": x.start, "end": x.end, "reason": x.reason}
                            )
                            for x in guard.error_spans_in_output()
                        ]
                        yield json.dumps(fragment_dict) + "\n"

                    call = guard.history.last
                    final_validation_output = ValidationOutcome(
                        callId=call.id,
                        validation_passed=result.validation_passed,
                        validated_output=result.validated_output,
                        history=guard.history,
                        raw_llm_output=result.raw_llm_output,
                    )
                    final_output_dict = final_validation_output.model_dump(
                        exclude_none=True, by_alias=True
                    )
                    final_output_dict["error_spans"] = [
                        json.dumps({"start": x.start, "end": x.end, "reason": x.reason})
                        for x in guard.error_spans_in_output()
                    ]
                    yield json.dumps(final_output_dict) + "\n"
                except Exception as e:
                    yield json.dumps({"error": {"message": str(e)}}) + "\n"

                if guard_history_is_enabled():
                    serialized_history = [
                        call.model_dump(exclude_none=True, by_alias=True)
                        for call in guard.history
                    ]
                    cache_key = f"{guard.id}-{final_validation_output.call_id}"
                    await cache_client.set(
                        cache_key, json.dumps(serialized_history), 300
                    )

            return StreamingResponse(
                validate_streamer(guard_streamer()), media_type="application/json"
            )
        else:
            execution = guard(
                prompt_params=prompt_params,
                num_reasks=num_reasks,
                *args,
                **payload,
            )
            if inspect.iscoroutine(execution):
                result: ValidationOutcome = await execution
            else:
                result: ValidationOutcome = execution
    if guard_history_is_enabled():
        serialized_history = [
            call.model_dump(exclude_none=True, by_alias=True) for call in guard.history
        ]
        cache_key = f"{guard.id}-{result.call_id}"
        await cache_client.set(cache_key, json.dumps(serialized_history), 300)
    result = attach_validation_summaries(result, guard)
    # result_dict = result.to_dict()
    # result_dict["validation_summaries"] = [
    #     vs.model_dump(exclude_none=True) for vs in result.validation_summaries or []
    # ]
    return result


# Deprecate this in favor of standard OTEL tracing
@router.get("/guards/{id}/history/{call_id}", deprecated=True)
@handle_error
async def guard_history(id: str, call_id: str) -> list[Call]:
    cache_key = f"{id}-{call_id}"
    cached_value = await cache_client.get(cache_key) or "[]"
    return json.loads(cached_value)
