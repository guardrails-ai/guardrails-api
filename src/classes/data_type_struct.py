from typing import Any, Dict, List
from operator import attrgetter
from guardrails.datatypes import DataType
from src.classes.schema_element_struct import SchemaElementStruct
from src.utils.pluck import pluck

class DataTypeStruct:
    def __init__(
        self,
        children: Dict[str, Any],
        formatters: List[str] = [],
        element: SchemaElementStruct = None
    ):
        self.children = children
        self.formatters = formatters
        self.element = element
    
    @classmethod
    def fromDataType(cls, dataType: DataType):
        xmlement = dataType.element
        name, description, strict, date_format, time_format, model = attrgetter(
          "name",
          "description",
          "strict",
          "date-format",
          "time-format",
          "model"
        )(xmlement)
        on_fail = ''
        for attr in xmlement.attrib:
            if attr.startswith("on-fail"):
                on_fail = attr
        return cls(
            dataType.children,
            dataType.format_attr.tokens,
            SchemaElementStruct(
            xmlement.tag,
            name,
            description,
            strict,
            date_format,
            time_format,
            on_fail,
            model
          )
        )
    
    @classmethod
    def from_dict(cls, dataType: dict):
        if dataType != None:
          children, formatters, element = pluck(
              dataType,
              [   
                "children",
                "formatters",
                "element"
              ]
          )
          serialied_children = {}
          if children != None:
            child_entries = children.get("item", {}) if element["type"] else children
            for child_key in child_entries:
                serialied_children[child_key] = cls.from_dict(child_entries[child_key])
          return cls(
              serialied_children,
              formatters,
              SchemaElementStruct.from_dict(element)
          )
    
    def to_dict(self):
        dict_children = {}
        elem_type = self.element.type if self.element != None else None
        if self.children != None:
          child_entries = self.children.get("item", {}) if elem_type == "list" else self.children
          for childKey in child_entries:
              dict_children[childKey] = child_entries[childKey].to_dict()
        return {
            "children": dict_children,
            "formatters": self.formatters,
            "element": self.element.to_dict()
        }
        
    