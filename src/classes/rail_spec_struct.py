from guardrails import Rail
from src.classes.schema_struct import SchemaStruct
from src.classes.base_prompt_struct import BasePromptStruct
from src.classes.script_struct import ScriptStruct
from src.utils.pluck import pluck

class RailSpecStruct:
    def __init__(
        self,
        input_schema: SchemaStruct = None,
        output_schema: SchemaStruct = None,
        instructions: BasePromptStruct = None,
        prompt: BasePromptStruct = None,
        script: ScriptStruct = None,
        version: str = "0.1",
    ):
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.instructions = instructions
        self.prompt = prompt
        self.script = script
        self.version = version
    
    @classmethod
    def from_rail(cls, rail: Rail):
        return cls(
          SchemaStruct.from_schema(rail.input_schema),
          SchemaStruct.from_schema(rail.output_schema),
          BasePromptStruct.from_prompt(rail.instructions),
          BasePromptStruct.from_prompt(rail.prompt),
          ScriptStruct.from_script(rail.script),
          rail.version
       )

    @classmethod
    def from_dict(cls, rail: dict):
        input_schema, output_schema, instructions, prompt, script, version = pluck(
            rail,
            [   
              "input_schema",
              "output_schema",
              "instructions",
              "prompt",
              "script",
              "version"
            ]
        )
        return cls(
          SchemaStruct.from_dict(input_schema),
          SchemaStruct.from_dict(output_schema),
          BasePromptStruct(instructions),
          BasePromptStruct(prompt),
          ScriptStruct.from_dict(script),
          version
       )
  
    def to_dict(self):
        rail = {
            "input_schema": None,
            "output_schema": None,
            "instructions": None,
            "prompt": None,
            "script": None,
            "version": self.version
        }

        if self.input_schema != None:
            rail["input_schema"] = self.input_schema.to_dict()
        if self.output_schema != None:
            rail["output_schema"] = self.output_schema.to_dict()
        if self.instructions != None:
            rail["instructions"] = self.instructions.to_dict()
        if self.prompt != None:
            rail["prompt"] = self.prompt.to_dict()
        if self.script != None:
            rail["script"] = self.script.to_dict()

        return rail
    
    @classmethod
    def from_request(cls, rail: dict):
        input_schema, output_schema, instructions, prompt, script, version = pluck(
            rail,
            [   
              "inputSchema",
              "outputSchema",
              "instructions",
              "prompt",
              "script",
              "version"
            ]
        )
        return cls(
          SchemaStruct.from_request(input_schema),
          SchemaStruct.from_request(output_schema),
          BasePromptStruct(instructions),
          BasePromptStruct(prompt),
          ScriptStruct.from_request(script),
          version
       )
    
    def to_response(self):
        rail = {
            "inputSchema": None,
            "outputSchema": None,
            "instructions": None,
            "prompt": None,
            "script": None,
            "version": self.version
        }

        if self.input_schema != None:
            rail["inputSchema"] = self.input_schema.to_response()
        if self.output_schema != None:
            rail["outputSchema"] = self.output_schema.to_response()
        if self.instructions != None:
            rail["instructions"] = self.instructions.to_response()
        if self.prompt != None:
            rail["prompt"] = self.prompt.to_response()
        if self.script != None:
            rail["script"] = self.script.to_response()

        return rail