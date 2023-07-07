from typing import Any, Dict, Optional
from lxml.etree import _Element
from src.utils.pluck import pluck

class ElementStub:
    def __init__(
            self,
            tag,
            attributes: Dict[str, Any]
            ) -> None:
        self.attrib = attributes
        self.tag = tag

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

    def to_element(self) -> _Element:
        elem_dict = self.to_dict()
        elem_dict["date-format"] = self.date_format
        elem_dict["time-format"] = self.time_format
        if self.on_fail_tag:
          elem_dict[self.on_fail_tag] = self.on_fail
        return ElementStub(self.type, elem_dict)

    @classmethod
    def from_dict(cls, schema_element: dict):
        if schema_element != None:
          type, name, description, strict, date_format, time_format, on_fail, on_fail_tag, model = pluck(
              schema_element,
              [      
                "type",
                "name",
                "description",
                "strict",
                "date_format",
                "time_format",
                "on_fail",
                "on_fail_tag",
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
              on_fail_tag,
              model
            )
    
    def to_dict(self):
        response = {
          "type": self.type,
          "name": self.name,
          "description": self.description,
        }

        if self.strict is not None:
          response["strict"] = self.strict
        if self.date_format is not None:
          response["date_format"] = self.date_format
        if self.time_format is not None:
          response["time_format"] = self.time_format
        if self.on_fail is not None:
          response["on_fail"] = self.on_fail
        if self.on_fail_tag is not None:
          response["on_fail_tag"] = self.on_fail_tag
        if self.model is not None:
          response["model"] = self.model

        return response
    
    @classmethod
    def from_request(cls, schema_element: dict):
        if schema_element != None:
          type, name, description, strict, date_format, time_format, on_fail, on_fail_tag, model = pluck(
              schema_element,
              [      
                "type",
                "name",
                "description",
                "strict",
                "dateFormat",
                "timeFormat",
                "onFail",
                "onFailTag",
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
              on_fail_tag,
              model
            )
        
    def to_response(self):
        response = {
          "type": self.type,
          "name": self.name,
          "description": self.description,
        }
        if self.strict is not None:
          response["strict"] = self.strict
        if self.dateFormat is not None:
          response["dateFormat"] = self.date_format
        if self.timeFormat is not None:
          response["timeFormat"] = self.time_format
        if self.onFail is not None:
          response["onFail"] = self.on_fail
        if self.onFailTag is not None:
          response["onFailTag"] = self.on_fail_tag
        if self.model is not None:
          response["model"] = self.model

        return response
    
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