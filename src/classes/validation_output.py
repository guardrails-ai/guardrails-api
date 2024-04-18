from typing import Union, Dict
from guardrails.classes.generic import Stack
from guardrails.classes.history import Call
from guardrails.utils.reask_utils import ReAsk

from src.utils.try_json_loads import try_json_loads


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
                        "output": (
                            i.outputs.raw_output
                            or (
                                i.outputs.llm_response_info.output
                                if i.outputs.llm_response_info is not None
                                else None
                            )
                        ),
                        "parsedOutput": i.parsed_output,
                        "prompt": {
                            "source": i.inputs.prompt.source
                            if i.inputs.prompt is not None
                            else None
                        },
                        "reasks": list(r.model_dump() for r in i.reasks),
                        "validatedOutput": i.guarded_output.model_dump()
                        if isinstance(i.guarded_output, ReAsk)
                        else i.guarded_output,
                        "failedValidations": list(
                            {
                                "validatorName": fv.validator_name,
                                "registeredName": fv.registered_name,
                                "valueBeforeValidation": fv.value_before_validation,
                                "validationResult": {
                                    "outcome": fv.validation_result.outcome,
                                    # Don't include metadata bc it could contain api keys
                                    # "metadata": fv.validation_result.metadata
                                },
                                "valueAfterValidation": fv.value_after_validation,
                                "startTime": (
                                    fv.start_time.isoformat()
                                    if fv.start_time
                                    else None
                                ),
                                "endTime": (
                                    fv.end_time.isoformat()
                                    if fv.end_time
                                    else None
                                ),
                                "instanceId": fv.instance_id,
                                "propertyPath": fv.property_path,
                            }
                            for fv in i.failed_validations
                        )
                    }
                    for i in c.iterations
                ]
            }
            for c in calls
        ]
        self.raw_llm_response = raw_llm_response
        self.validated_stream = [
            {
                "chunk": raw_llm_response,
                "validation_errors": [
                    try_json_loads(fv.validation_result.error_message)
                    for fv in c.iterations.last.failed_validations
                ]
            }
            for c in calls
        ]

    def to_response(self):
        return {
            "result": self.result,
            "validatedOutput": self.validated_output,
            "sessionHistory": self.session_history,
            "rawLlmResponse": self.raw_llm_response,
            "validatedStream": self.validated_stream,
        }
