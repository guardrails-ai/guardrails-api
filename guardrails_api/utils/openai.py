import contextvars
from functools import partial
from typing import Any

from guardrails import AsyncGuard, Guard
from guardrails.classes import ValidationOutcome
from litellm import Choices
import litellm

from guardrails_api.classes.http_error import HttpError


def outcome_to_stream_response(validation_outcome: ValidationOutcome):
    stream_chunk_template = {
        "choices": [
            {
                "delta": {
                    "content": validation_outcome.validated_output,
                },
            }
        ],
        "guardrails": {
            "reask": validation_outcome.reask or None,
            "validation_passed": validation_outcome.validation_passed,
            "error": validation_outcome.error or None,
        },
    }
    # does this even make sense with a stream? wed need each chunk as theyre emitted
    stream_chunk = stream_chunk_template
    stream_chunk["choices"][0]["delta"]["content"] = validation_outcome.validated_output
    return stream_chunk


def outcome_to_chat_completion(
    validation_outcome: ValidationOutcome,
    llm_response,
    has_tool_gd_tool_call=False,
):
    completion_template = (
        {"choices": [{"message": {"content": ""}}]}
        if not has_tool_gd_tool_call
        else {
            "choices": [{"message": {"tool_calls": [{"function": {"arguments": ""}}]}}]
        }
    )
    completion = getattr(llm_response, "full_raw_llm_output", completion_template)
    completion["guardrails"] = {
        "reask": validation_outcome.reask or None,
        "validation_passed": validation_outcome.validation_passed,
        "error": validation_outcome.error or None,
        "validation_summaries": [
            summary.model_dump()
            for summary in (validation_outcome.validation_summaries or [])
        ],
    }

    # string completion
    try:
        completion["choices"][0]["message"]["content"] = (
            validation_outcome.validated_output
        )
    except KeyError:
        pass

    # tool completion
    try:
        choice = completion["choices"][0]
        # if this is accessible it means a tool was called so set our validated output to that
        choice["message"]["tool_calls"][-1]["function"]["arguments"] = (
            validation_outcome.validated_output
        )
    except KeyError:
        pass

    return completion


def get_chat_completion_output(choice: Choices) -> str | None:
    output = None
    if choice.message.content is not None:  # type: ignore
        output = choice.message.content  # type: ignore
    else:
        try:
            output = choice.message.function_call.arguments  # type: ignore
        except AttributeError:
            try:
                output = choice.message.tool_calls[-1].function.arguments  # type: ignore
            except AttributeError:
                pass
    return output


async def guarded_chat_completion(
    guard: Guard | AsyncGuard, payload: Any
) -> dict[str, Any]:
    ctx_chat_completion = contextvars.ContextVar("x_guardrails_api_ctx_chat_completion")
    ctx = contextvars.copy_context()

    def llm_wrapper(ctx_var, *args, messages, **kwargs) -> str:
        chat_completion = litellm.completion(*args, messages=messages, **kwargs)  # type: ignore
        ctx_var.set(chat_completion)
        choice = chat_completion.choices[0]  # type: ignore

        output = ""
        if choice.message.content is not None:  # type: ignore
            output = choice.message.content  # type: ignore
        else:
            try:
                output = choice.message.function_call.arguments  # type: ignore
            except AttributeError:
                try:
                    output = choice.message.tool_calls[-1].function.arguments  # type: ignore
                except AttributeError:
                    pass
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
