from typing import List, Union, Dict
from guardrails import Instructions
from guardrails.utils.logs_utils import GuardHistory
from guardrails.utils.reask_utils import ReAsk


class ValidationOutput:
    def __init__(
        self,
        result: bool,
        validated_output: Union[str, Dict, ReAsk],
        histories: List[GuardHistory] = None,
        raw_llm_response: str = None,
    ):
        self.result = result
        self.validated_output = (
            validated_output.dict()
            if isinstance(validated_output, ReAsk)
            else validated_output
        )
        self.session_history = [
            {
                "history": [
                    {
                        "instructions": h.instructions.source
                        if isinstance(h.instructions, Instructions)
                        else h.instructions,
                        "output": h.output,
                        "parsedOutput": h.parsed_output.dict()
                        if isinstance(h.parsed_output, ReAsk)
                        else h.parsed_output,
                        "prompt": {
                            "source": h.prompt.source
                            if h.prompt is not None
                            else None
                        },
                        "reasks": list(r.dict() for r in h.reasks),
                        "validatedOutput": h.validated_output.dict()
                        if isinstance(h.validated_output, ReAsk)
                        else h.validated_output,
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
