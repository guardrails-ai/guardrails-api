from typing import Any, Dict, List
from operator import attrgetter
from guardrails.datatypes import DataType
from src.classes.schema_element_struct import SchemaElementStruct
from src.utils.pluck import pluck

class DataTypeStruct:
    def __init__(
        self,
        children: Dict[str, Any] = None,
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
          children_data_types = None
          if children != None:
            class_children = {}
            elem_type = element["type"] if element != None else None
            elem_is_list = elem_type == "list"
            child_entries = children.get("item", {}) if elem_is_list else children
            for child_key in child_entries:
                class_children[child_key] = cls.from_dict(child_entries[child_key])
            children_data_types = { "item": class_children } if elem_is_list else class_children
          return cls(
              children_data_types,
              formatters,
              SchemaElementStruct.from_dict(element)
          )
    
    def to_dict(self):
        response = {
           "formatters": self.formatters,
            "element": self.element.to_dict()
        }
        if self.children != None:
          serialized_children = {}
          elem_type = self.element.type if self.element != None else None
          elem_is_list = elem_type == "list"
          child_entries = self.children.get("item", {}) if elem_is_list else self.children
          for childKey in child_entries:
              serialized_children[childKey] = child_entries[childKey].to_dict()
          response["children"] = { "item": serialized_children } if elem_is_list else serialized_children
        return response
    
    @classmethod
    def from_request(cls, dataType: dict):
        if dataType != None:
          children, formatters, element = pluck(
              dataType,
              [   
                "children",
                "formatters",
                "element"
              ]
          )
          children_data_types = None
          if children != None:
            class_children = {}
            elem_type = element["type"] if element != None else None
            elem_is_list = elem_type == "list"
            child_entries = children.get("item", {}) if element["type"] else children
            for child_key in child_entries:
                class_children[child_key] = cls.from_request(child_entries[child_key])
            children_data_types = { "item": class_children } if elem_is_list else class_children
          
          return cls (
              children_data_types,
              formatters,
              SchemaElementStruct.from_request(element)
          )
        
    def to_response(self):
        response = {
            "formatters": self.formatters,
            "element": self.element.to_response()
        }
        if self.children != None:
          serialized_children = {}
          elem_type = self.element.type if self.element != None else None
          elem_is_list = elem_type == "list"
          child_entries = self.children.get("item", {}) if elem_type == "list" else self.children
          for childKey in child_entries:
              serialized_children[childKey] = child_entries[childKey].to_response()
          children_resposne = { "item": serialized_children } if elem_is_list else serialized_children
          response["children"]: children_resposne
        return response
        
    