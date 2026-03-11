import contextvars
from functools import partial
import json
from typing import Any, AsyncGenerator, Iterator

from guardrails import AsyncGuard, Guard
from guardrails.classes import ValidationOutcome

from guardrails.classes.validation.validation_summary import ValidationSummary
from litellm import Choices, CustomStreamWrapper, ModelResponse, StreamingChoices
import litellm

from guardrails_api.classes.http_error import HttpError

ctx_chat_completion = contextvars.ContextVar("x_guardrails_api_ctx_chat_completion")
ctx_chat_completion_stream = contextvars.ContextVar(
    "x_guardrails_api_ctx_chat_completion_stream"
)

ctx = contextvars.copy_context()


async def guarded_chat_completion(
    guard: Guard | AsyncGuard, payload: Any
) -> dict[str, Any]:

    def llm_wrapper(ctx_var, *args, messages, **kwargs) -> str:
        # We know this is not a streaming respons, hence the type ignores
        chat_completion: ModelResponse = litellm.completion(
            *args, messages=messages, **kwargs
        )  # type: ignore
        ctx_var.set(chat_completion)
        choice: Choices = chat_completion.choices[0]  # type: ignore

        output = ""
        message = choice.message
        if message.content is not None:
            output = message.content
        elif message.function_call and message.function_call.arguments is not None:
            output = message.function_call.arguments
        elif (
            message.tool_calls and message.tool_calls[-1].function.arguments is not None
        ):
            output = message.tool_calls[-1].function.arguments
        return output

    async def async_llm_wrapper(ctx_var, *args, messages, **kwargs) -> str:
        return llm_wrapper(ctx_var, *args, messages=messages, **kwargs)

    async def run_guard():
        if isinstance(guard, AsyncGuard):
            llm_api = partial(async_llm_wrapper, ctx_chat_completion)
            validation_outcome: ValidationOutcome = await guard(
                num_reasks=0, llm_api=llm_api, **payload
            )  # type: ignore
        else:
            llm_api = partial(llm_wrapper, ctx_chat_completion)
            validation_outcome: ValidationOutcome = guard(
                num_reasks=0, llm_api=llm_api, **payload
            )  # type: ignore

        chat_completion = ctx_chat_completion.get()
        if not chat_completion:
            raise HttpError(
                status=500,
                message="The model did not return any message content, function call arguments, or tool call arguments.",
            )

        completion = chat_completion.model_dump()
        completion["guardrails"] = validation_outcome.model_dump()

        return completion

    return await ctx.run(run_guard)


async def guarded_chat_completion_stream(
    guard: Guard | AsyncGuard, payload: Any
) -> AsyncGenerator[str]:
    # Async Streaming for custom llm callables it broken in guardrails-ai<=0.9.1
    # We just force it to be synchronous for now
    _guard: Guard
    if isinstance(guard, AsyncGuard):
        _guard: Guard = Guard.from_dict(guard.to_dict())  # type: ignore
    else:
        _guard = guard

    def llm_wrapper(*args, messages, **kwargs) -> Iterator[str]:
        # We know this _is_ a streaming response, hence the type ignores
        chat_completion_stream: CustomStreamWrapper = litellm.completion(
            *args, messages=messages, **kwargs
        )  # type: ignore
        for chunk in chat_completion_stream:
            ctx_chat_completion_stream.set(chunk)
            choice: StreamingChoices = chunk.choices[0]

            output = ""
            delta = choice.delta
            if delta.content is not None:
                output = delta.content
            elif delta.function_call and delta.function_call.arguments is not None:
                output = delta.function_call.arguments
            elif (
                delta.tool_calls and delta.tool_calls[-1].function.arguments is not None
            ):
                output = delta.tool_calls[-1].function.arguments
            yield output

    async def run_guard():
        guard_stream: Iterator[ValidationOutcome] = _guard(
            num_reasks=0, llm_api=llm_wrapper, **payload
        )  # type: ignore
        validator_logs = []
        for result in guard_stream:
            chunk = ctx_chat_completion_stream.get()
            ser_chunk = chunk.model_dump()

            v_logs = _guard.history.last.validator_logs if _guard.history.last else []
            new_v_logs = [log for log in v_logs if log not in validator_logs]
            validator_logs.extend(new_v_logs)
            # TODO: Replace with guardrails_api.utils.attach_validation_summaries.attach_validation_summaries once we figure out why we can't just drop it in without duplications
            if not result.validation_summaries:
                result.validation_summaries = (
                    ValidationSummary.from_validator_logs_only_fails(new_v_logs)
                )
            ser_chunk["guardrails"] = result.model_dump()
            yield f"data: {json.dumps(ser_chunk)}\n\n"
        yield "\n"

    return ctx.run(run_guard)
