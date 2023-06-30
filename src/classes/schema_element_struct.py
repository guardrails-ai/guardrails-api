from typing import Optional
from lxml.etree import _Element
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
        on_fail_tag: Optional[str],
        model: Optional[str],
    ):
        self.type = type
        self.name = name
        self.description = description
        self.strict = strict
        self.date_format = date_format
        self.time_format = time_format
        self.on_fail = on_fail
        self.on_fail_tag = on_fail_tag
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
    
    @classmethod
    def from_request(cls, schema_element: dict):
        if schema_element != None:
          type, name, description, strict, date_format, time_format, on_fail, model = pluck(
              schema_element,
              [      
                "type",
                "name",
                "description",
                "strict",
                "dateFormat",
                "timeFormat",
                "onFail",
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
        
    def to_response(self):
        return {
          "type": self.type,
          "name": self.name,
          "description": self.description,
          "strict": self.strict,
          "dateFormat": self.date_format,
          "timeFormat": self.time_format,
          "onFail": self.on_fail,
          "model": self.model   
        }
    
    @classmethod
    def from_xml(cls, xml: _Element):
        type = xml.tag
        name = xml.get("name")
        description = xml.get("name")
        strict = None
        strict_tag = xml.get("strict")
        if strict_tag:
            strict = True if strict_tag == "true" else False
        date_format = xml.get("date-format")
        time_format  = xml.get("time-format")
        on_fail = None
        on_fail_tag = None
        attr_keys = xml.keys()
        for attr_key in attr_keys:
            if attr_key.startswith("on-fail"):
                on_fail = xml.get(attr_key)
                on_fail_tag = attr_key
        model = xml.get("model")
        return cls(
            type,
            name,
            description,
            strict,
            date_format,
            time_format,
            on_fail,
            on_fail_tag,
            model
        )