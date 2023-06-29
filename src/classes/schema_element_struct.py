from typing import Optional
from src.utils.pluck import pluck

class SchemaElementStruct:
    def __init__(
        self,
        type: str,
        name: str,
        description: str,
        strict: Optional[bool],
        date_format: Optional[str],
        time_format: Optional[str],
        on_fail: Optional[str],
        model: Optional[str],
    ):
        self.type = type
        self.name = name
        self.description = description
        self.strict = strict
        self.date_format = date_format
        self.time_format = time_format
        self.on_fail = on_fail
        self.model = model

    @classmethod
    def from_dict(cls, schema_element: dict):
        if schema_element != None:
          type, name, description, strict, date_format, time_format, on_fail, model = pluck(
              schema_element,
              [      
                "type",
                "name",
                "description",
                "strict",
                "date_format",
                "time_format",
                "on_fail",
                "model"
              ]
          )
          return cls(
              type,
              name,
              description,
              strict,
              date_format,
              time_format,
              on_fail,
              model
            )
    
    def to_dict(self):
        return {
          "type": self.type,
          "name": self.name,
          "description": self.description,
          "strict": self.strict,
          "date_format": self.date_format,
          "time_format": self.time_format,
          "on_fail": self.on_fail,
          "model": self.model   
        }