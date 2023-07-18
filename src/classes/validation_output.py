from typing import List
from guardrails.utils.logs_utils import GuardHistory


class ValidationOutput:
    def __init__(
        self,
        result: bool,
        validated_output: dict,
        histories: List[GuardHistory] = None,
        raw_llm_response: str = None,
    ):
        self.result = result
        self.validated_output = validated_output
        self.session_history = [
            {
                "history": [
                    {
                        "instructions": h.instructions,
                        "output": h.output,
                        "parsedOutput": h.parsed_output,
                        "prompt": {
                            "source": h.prompt.source
                            if h.prompt is not None
                            else None
                        },
                        "reasks": h.reasks,
                        "validatedOutput": h.validated_output,
                    }
                    for h in x.history
                ]
            }
            for x in histories
        ]
        self.raw_llm_response = raw_llm_response

    def to_response(self):
        return {
            "result": self.result,
            "validatedOutput": self.validated_output,
            "sessionHistory": self.session_history,
            "rawLlmResponse": self.raw_llm_response,
        }
