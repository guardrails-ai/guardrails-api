from guardrails.rail import Script
from lxml.etree import _Element


class ScriptStruct:
    def __init__(self, text: str, language: str, variables: dict):
        self.text = text
        self.language = language
        self.variables = variables

    @classmethod
    def from_script(cls, script: Script):
        return cls(
            None,  # the script text is not accessible from the Script class
            script.language,
            script.variables,
        )

    @classmethod
    def from_dict(cls, script: dict):
        if script is not None:
            return cls(script["text"], script["language"], script["variables"])

    def to_dict(self):
        return {
            "text": self.text,
            "language": self.language,
            "variables": self.variables,
        }

    @classmethod
    def from_request(cls, script: dict):
        return cls.from_dict(script)

    def to_response(self):
        return self.to_dict()

    @classmethod
    def from_xml(cls, elem: _Element):
        if "language" not in elem.attrib:
            raise ValueError("Script element must have a language attribute.")

        language = elem.get("language")
        if language != "python":
            raise ValueError("Only python scripts are supported right now.")

        return cls(elem.text, language, {})
