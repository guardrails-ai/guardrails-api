from typing import List, Dict, Any
from guardrails.classes import ValidationOutcome

def outcome_to_stream_response(validation_outcome: ValidationOutcome):
    stream_chunk_template ={
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
    stream_chunk = getattr(validation_outcome, "full_raw_llm_output", stream_chunk_template)
    stream_chunk["choices"][0]["delta"]["content"] = validation_outcome.validated_output
    return stream_chunk

def outcome_to_chat_completion(validation_outcome: ValidationOutcome, has_tool_gd_tool_call=False,):
    completion_template = {
        "choices": [{"message": {"content": ""}}]
    } if not has_tool_gd_tool_call else {
        "choices": [{"message": {"tool_calls": [{"function": {"arguments": ""}}]}}]
    }
    completion = getattr(validation_outcome, "full_raw_llm_output", completion_template)
    completion["guardrails"] = {
        "reask": validation_outcome.reask or None,
        "validation_passed": validation_outcome.validation_passed,
        "error": validation_outcome.error or None,
    }
    
    # string completion
    try:
        completion["choices"][0]["message"]["content"] = validation_outcome.validated_output
    except:
        pass
    
    # tool completion
    try:
        choice = completion["choices"][0]
        # if this is accessible it means a tool was called so set our validated output to that
        choice["message"]["tool_calls"][-1]["function"]["arguments"] = validation_outcome.validated_output
    except:
        pass

    return completion