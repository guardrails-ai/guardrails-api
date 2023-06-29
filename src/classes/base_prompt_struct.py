from guardrails.prompt.base_prompt import BasePrompt


class BasePromptStruct:
    def __init__(
        self,
        source: str,
        output_schema: str = None
    ):
        self.source = source
        self.output_schema = output_schema

    @classmethod
    def from_prompt(cls, prompt: BasePrompt):
        return cls(
            prompt.source,
            None # the output_schema isn't assigned to the BasePrompt class and thereform not accessible
        )
    
    def to_dict(self):
        return {
            "source": self.source,
            "output_schema": self.output_schema
        }
    
    def to_response(self):
        return {
            "source": self.source,
            "outputSchema": self.output_schema
        }