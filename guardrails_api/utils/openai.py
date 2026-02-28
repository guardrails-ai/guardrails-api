import time
import uuid

from guardrails.classes import ValidationOutcome


def _ensure_openai_fields(response: dict, object_type: str = "chat.completion"):
    """Ensure the response contains required OpenAI-compatible fields.

    Per the OpenAI API spec, responses must include ``id``, ``object``,
    ``created``, and ``model``.  When the upstream LLM response already
    provides these fields they are preserved; otherwise sensible defaults
    are injected.
    """
    response.setdefault("id", f"chatcmpl-{uuid.uuid4().hex}")
    response.setdefault("object", object_type)
    response.setdefault("created", int(time.time()))
    response.setdefault("model", "guardrails")


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
    _ensure_openai_fields(stream_chunk, object_type="chat.completion.chunk")
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
    _ensure_openai_fields(completion)
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
