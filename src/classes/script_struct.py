from guardrails.rail import Script


class ScriptStruct:
    def __init__(
        self,
        text: str,
        language: str,
        variables: dict
    ):
        self.text = text
        self.language = language
        self.variables = variables

    @classmethod
    def from_script(cls, script: Script):
        return cls(
            None, # the script text isn't assigned to the Script class and thereform not accessible
            script.language,
            script.variables
        )

    @classmethod
    def from_dict(cls, script: dict):
        if script != None:
          return cls(
              script["text"],
              script["language"],
              script["variables"]
          )

    def to_dict(self):
        return {
          "text": self.text,
          "language": self.language,
          "variables": self.variables   
        }