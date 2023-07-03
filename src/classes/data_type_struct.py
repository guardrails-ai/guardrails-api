import re
from typing import Any, Dict, List
from operator import attrgetter
from lxml.etree import _Element
from guardrails.datatypes import DataType, registry
from guardrails.schema import FormatAttr
from src.classes.schema_element_struct import ElementStub, SchemaElementStruct
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
    def from_data_type(cls, dataType: DataType):
        xmlement = dataType.element
        name, description, strict, date_format, time_format, model = attrgetter(
          "name",
          "description",
          "strict",
          "date-format",
          "time-format",
          "model"
        )(xmlement)
        on_fail = None
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
    
    def to_data_type(self) -> DataType:
      data_type = None

      element = self.element.to_element()

      format = "; ".join(self.formatters)
      format_attr = FormatAttr(format)
      format_attr.element = element
      format_attr.get_validators(self.element.strict)
      
      self_is_list = self.element.type == 'list'
      children = None
      if self.children:
        children = {}
        child_entries = self.children.get("item", {}) if self_is_list else self.children
        for child_key in child_entries:
           children[child_key] = child_entries[child_key].to_data_type()
        # FIXME: For Lists where the item type is not an object

      if self_is_list:
         object_element = ElementStub('object', {})
         object_format_attr = FormatAttr(format)
         object_format_attr.element = object_element
         object_format_attr.get_validators()
         object_data_type = registry['object'](children=children, format_attr=object_format_attr, element=object_element)
         children = { "item": object_data_type }

      data_type_cls = registry[self.element.type]
      if data_type_cls != None:
        data_type = data_type_cls(children=children, format_attr=format_attr, element=element)
        if self.element.type == "date":
          data_type.date_format = self.element.date_format if self.element.date_format else data_type.date_format
        elif self.element.type == "time":
           data_type.time_format = self.element.time_format if self.element.time_format else data_type.time_format

      return data_type
       
    
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
          for child_key in child_entries:
              serialized_children[child_key] = child_entries[child_key].to_dict()
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
          child_entries = self.children.get("item", {}) if elem_is_list else self.children
          for child_key in child_entries:
              serialized_children[child_key] = child_entries[child_key].to_response()
          response["children"] = { "item": serialized_children } if elem_is_list else serialized_children
        return response
        
    @classmethod
    def from_xml(cls, elem: _Element):
      elem_format = elem.get("format", "")
      pattern = re.compile(r";(?![^{}]*})")
      tokens = re.split(pattern, elem_format)
      formatters = list(filter(None, tokens))

      element = SchemaElementStruct.from_xml(elem)
      
      elem_type = elem.tag
      elem_is_list = elem_type == 'list'
      children = None
      elem_children = list(elem) # Not strictly necessary but more readable
      if (len(elem_children) > 0):
        if elem_is_list:
           children = { "item": cls.from_xml(elem_children[0]).children }
        else:
          children = {}
          child: _Element
          for child in elem_children:
            child_key = child.get("name")
            children[child_key] = cls.from_xml(child)

      return cls(
        children,
        formatters,
        element
      )