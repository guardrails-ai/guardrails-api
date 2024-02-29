from typing import Union, Dict
from guardrails.classes.generic import Stack
from guardrails.classes.history import Call
from guardrails.utils.reask_utils import ReAsk


class ValidationOutput:
    def __init__(
        self,
        result: bool,
        validated_output: Union[str, Dict, None],
        calls: Stack[Call] = Stack(),
        raw_llm_response: str = None,
    ):
        self.result = result
        self.validated_output = validated_output
        self.session_history = [
            {
                "history": [
                    {
                        "instructions": i.inputs.instructions.source
                        if i.inputs.instructions is not None
                        else None,
                        "output": i.outputs.raw_output or i.outputs.llm_response_info.output,
                        "parsedOutput": i.parsed_output,
                        "prompt": {
                            "source": i.inputs.prompt.source
                            if i.inputs.prompt is not None
                            else None
                        },
                        "reasks": list(r.dict() for r in i.reasks),
                        "validatedOutput": i.validated_output.dict()
                        if isinstance(i.validated_output, ReAsk)
                        else i.validated_output,
                    }
                    for i in c.iterations
                ]
            }
            for c in calls
        ]
        self.raw_llm_response = raw_llm_response

    def to_response(self):
        return {
            "result": self.result,
            "validatedOutput": self.validated_output,
            "sessionHistory": self.session_history,
            "rawLlmResponse": self.raw_llm_response,
        }
