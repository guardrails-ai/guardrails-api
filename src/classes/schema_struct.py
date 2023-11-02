from typing import Dict, List, Union
from lxml.etree import _Element, _Comment, SubElement
from guardrails.schema import Schema, StringSchema, JsonSchema
from src.classes.data_type_struct import DataTypeStruct


# TODO: Rather than a custom schema construct like what this is now
# consider making this JSONSchema
# https://json-schema.org/
class SchemaStruct:
    schema: Union[Dict[str, DataTypeStruct], DataTypeStruct] = None

    def __init__(self, schema: Dict[str, DataTypeStruct] = None):
        self.schema = schema

    @classmethod
    def from_schema(cls, schema: Schema):
        serialized_schema = {}

        if isinstance(schema, StringSchema):
            serialized_schema = DataTypeStruct.from_data_type(
                schema
            )
        else:
            for key in schema._schema:
                schema_element = schema._schema[key]
                serialized_schema[key] = DataTypeStruct.from_data_type(
                    schema_element
                )
        return cls({"schema": serialized_schema})

    def to_schema(self) -> Schema:
        schema = {}
        inner_schema = self.schema["schema"]

        if isinstance(inner_schema, DataTypeStruct):
            string_schema = StringSchema()
            string_schema.string_key = inner_schema.element.name
            string_schema[
                string_schema.string_key
            ] = inner_schema.to_data_type()
            return string_schema

        for key in inner_schema:
            schema_element: DataTypeStruct = inner_schema[key]
            schema[key] = schema_element.to_data_type()

        return JsonSchema(schema=schema)

    @classmethod
    def from_dict(cls, schema: dict):
        if schema is not None:
            serialized_schema = {}
            inner_schema = schema["schema"]
            if DataTypeStruct.is_data_type_struct(inner_schema):
                serialized_schema = DataTypeStruct.from_dict(
                    inner_schema
                )
            else:
                for key in inner_schema:
                    schema_element = inner_schema[key]
                    serialized_schema[key] = DataTypeStruct.from_dict(
                        schema_element
                    )
            return cls({"schema": serialized_schema})

    def to_dict(self):
        dict_schema = {}
        inner_schema = self.schema["schema"]
        if isinstance(inner_schema, DataTypeStruct):
            dict_schema = inner_schema.to_dict()
        else:
            for key in inner_schema:
                schema_element = inner_schema[key]
                dict_schema[key] = schema_element.to_dict()
        return {"schema": dict_schema}

    @classmethod
    def from_request(cls, schema: dict):
        if schema is not None:
            serialized_schema = {}
            inner_schema = schema["schema"]

            # StringSchema (or really just any PrimitiveSchema)
            if DataTypeStruct.is_data_type_struct(inner_schema):
                serialized_schema = DataTypeStruct.from_request(
                    inner_schema
                )
            else:
                # JsonSchema
                for key in inner_schema:
                    schema_element = inner_schema[key]
                    serialized_schema[key] = DataTypeStruct.from_request(
                        schema_element
                    )
            return cls({"schema": serialized_schema})

    def to_response(self):
        dict_schema = {}
        inner_schema = self.schema["schema"]
        if isinstance(inner_schema, DataTypeStruct):
            dict_schema = inner_schema.to_response()
        else:
            for key in inner_schema:
                schema_element = inner_schema[key]
                dict_schema[key] = schema_element.to_response()
        return {"schema": dict_schema}

    # FIXME: if this is ever used it needs to be updated to handle StringSchemas
    @classmethod
    def from_xml(cls, xml: _Element):
        schema = {}
        child: _Element
        for child in xml:
            if isinstance(child, _Comment):
                continue
            name = child.get("name")
            schema[name] = DataTypeStruct.from_xml(child)

        return cls({"schema": schema})

    def to_xml(self, parent: _Element, tag: str) -> _Element:
        xml_schema = SubElement(parent, tag)
        inner_schema = self.schema["schema"]
        if isinstance(inner_schema, DataTypeStruct):
            inner_schema.to_xml(xml_schema, True)
        else:
            for key in inner_schema:
                child: DataTypeStruct = inner_schema[key]
                child.to_xml(xml_schema)

        return xml_schema

    def get_all_plugins(self) -> List[str]:
        plugins = []
        inner_schema = self.schema["schema"]

        if isinstance(inner_schema, DataTypeStruct):
            plugins.extend(inner_schema.get_all_plugins())
        else:
            for key in inner_schema:
                schema_element: DataTypeStruct = inner_schema[key]
                plugins.extend(schema_element.get_all_plugins())
        return plugins
