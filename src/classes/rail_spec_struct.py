from guardrails import Instructions, Prompt, Rail
from lxml import etree
from src.classes.schema_struct import SchemaStruct
from src.classes.script_struct import ScriptStruct
from src.utils.pluck import pluck

class RailSpecStruct:
    def __init__(
        self,
        input_schema: SchemaStruct = None,
        output_schema: SchemaStruct = None,
        instructions: str = None,
        prompt: str = None,
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
          rail.instructions.source,
          rail.prompt.source,
          ScriptStruct.from_script(rail.script),
          rail.version
       )

    def to_rail(self) -> Rail:
        input_schema = self.input_schema.to_schema() if self.input_schema else None
        output_schema = self.output_schema.to_schema() if self.output_schema else None
        instructions = Instructions(self.instructions, output_schema) if self.instructions else None
        prompt = Prompt(self.prompt, output_schema) if self.prompt else None
        script = self.script.to_script() if self.script else None
        return Rail(
            input_schema,
            output_schema,
            instructions,
            prompt,
            script,
            self.version
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
          instructions,
          prompt,
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
            rail["instructions"] = self.instructions
        if self.prompt != None:
            rail["prompt"] = self.prompt
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
          instructions,
          prompt,
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
            rail["instructions"] = self.instructions
        if self.prompt != None:
            rail["prompt"] = self.prompt
        if self.script != None:
            rail["script"] = self.script.to_response()

        return rail
    
    @classmethod
    def from_xml(cls, railspec: str):
        XMLPARSER = etree.XMLParser(encoding="utf-8")
        elem_tree = etree.fromstring(railspec, parser=XMLPARSER)

        if "version" not in elem_tree.attrib or elem_tree.attrib["version"] != "0.1":
            raise ValueError(
                "RAIL file must have a version attribute set to 0.1."
                "Change the opening <rail> element to: <rail version='0.1'>."
            )

        # Load <input /> schema
        input_schema = None
        raw_input_schema = elem_tree.find("input")
        if raw_input_schema is not None:
            input_schema = SchemaStruct.from_xml(raw_input_schema)

        # Load <output /> schema
        output_schema = None
        raw_output_schema = elem_tree.find("output")
        if raw_output_schema is not None:
            output_schema = SchemaStruct.from_xml(raw_output_schema)
        
        
        # Parse instructions for the LLM. These are optional but if given,
        # LLMs can use them to improve their output. Commonly these are
        # prepended to the prompt.
        instructions_elem = elem_tree.find("instructions")
        instructions = None
        if instructions_elem is not None:
            instructions = instructions.text

        # Load <prompt />
        prompt = elem_tree.find("prompt")
        if prompt is None:
            raise ValueError("RAIL file must contain a prompt element.")
        prompt = prompt.text

        # Execute the script before validating the rest of the RAIL file.
        script = None
        raw_script = elem_tree.find("script")
        if raw_script is not None:
            script = ScriptStruct.from_xml(raw_script)

        return cls(
            input_schema=input_schema,
            output_schema=output_schema,
            instructions=instructions,
            prompt=prompt,
            script=script,
            version=elem_tree.attrib["version"]
        )