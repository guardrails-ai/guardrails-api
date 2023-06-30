from typing import Dict
from guardrails.schema import Schema
from src.classes.data_type_struct import DataTypeStruct

# TODO: Rather than a custom schema construct like what this is now, consider making this JSONSchema
# https://json-schema.org/
class SchemaStruct:
    schema: Dict[str, DataTypeStruct] = None
    def __init__(
        self,
        schema: Dict[str, DataTypeStruct] = None
    ):
        self.schema = schema

    @classmethod
    def from_schema(cls, schema: Schema):
        serialized_schema = {}
        for key in schema._schema:
            schema_element = schema._schema[key]
            serialized_schema[key] = DataTypeStruct.fromDataType(schema_element)
        return cls(
            { "schema": serialized_schema }
        )

    @classmethod
    def from_dict(cls, schema: dict):
        if schema != None:
          serialized_schema = {}
          orig_schema = schema["schema"]
          for key in orig_schema:
              schema_element = orig_schema[key]
              serialized_schema[key] = DataTypeStruct.from_dict(schema_element)
          return cls(
              { "schema": serialized_schema }
          )
    
    def to_dict(self):
      dict_schema = {}
      inner_schema = self.schema["schema"]
      for key in inner_schema:
          schema_element = inner_schema[key]
          dict_schema[key] = schema_element.to_dict()
      return { "schema": dict_schema }
    
    @classmethod
    def from_request(cls, schema: dict):
      if schema != None:
        serialized_schema = {}
        inner_schema = schema["schema"]
        for key in inner_schema:
            schema_element = inner_schema[key]
            serialized_schema[key] = DataTypeStruct.from_request(schema_element)
        return cls(
            { "schema": serialized_schema }
        )
      
    def to_response(self):
      dict_schema = {}
      for key in self.schema["schema"]:
          schema_element = self.schema[key]
          dict_schema[key] = schema_element.to_response()
      return { "schema": dict_schema }