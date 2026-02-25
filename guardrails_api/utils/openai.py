import inspect
from typing import Any

from guardrails import AsyncGuard, Guard
from guardrails.classes import ValidationOutcome
from litellm import Choices, ModelResponse


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


async def validate_chat_completion(
    chat_completion: ModelResponse, guard: Guard | AsyncGuard, payload: Any
) -> dict[str, Any]:
    validations = []
    for choice in chat_completion.choices:
        output = get_chat_completion_output(choice)  # type: ignore

        if not output:
            validations.append(
                {
                    "reask": None,
                    "validation_passed": False,
                    "error": "The model did not return any message content, function call arguments, or tool call arguments.",
                    "validation_summaries": [],
                }
            )
            continue

        execution = guard.validate(output)
        if inspect.iscoroutine(execution):
            validation_outcome: ValidationOutcome = await execution  # type: ignore
        else:
            validation_outcome: ValidationOutcome = execution

        validations.append(validation_outcome.model_dump())

    completion = chat_completion.model_dump()
    if len(validations) > 1:
        completion["guardrails"] = validations
    else:
        completion["guardrails"] = validations[0]

    return completion
