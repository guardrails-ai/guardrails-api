import re
from typing import Any, Dict, List, Optional
from operator import attrgetter
from lxml.etree import _Element, SubElement
from guardrails.datatypes import DataType, registry
from guardrails.validatorsattr import ValidatorsAttr
from src.classes.schema_element_struct import SchemaElementStruct
from src.classes.element_stub import ElementStub
from src.utils.pluck import pluck


class DataTypeStruct:
    children: Dict[str, Any] = None
    formatters: List[str] = None
    element: SchemaElementStruct = None
    plugins: List[str] = None

    def __init__(
        self,
        children: Dict[str, Any] = None,
        formatters: List[str] = [],
        element: SchemaElementStruct = None,
        plugins: List[str] = None,
    ):
        self.children = children
        self.formatters = formatters
        self.element = element
        self.plugins = plugins

    @classmethod
    def from_data_type(cls, data_type: DataType):
        xmlement = data_type.element
        name, description, strict, date_format, time_format, model = attrgetter(
            "name",
            "description",
            "strict",
            "date-format",
            "time-format",
            "model",
        )(xmlement)
        on_fail = None
        for attr in xmlement.attrib:
            if attr.startswith("on-fail"):
                on_fail = attr
        return cls(
            children=data_type.children,
            formatters=data_type.format_attr.tokens,
            element=SchemaElementStruct(
                xmlement.tag,
                name,
                description,
                strict,
                date_format,
                time_format,
                on_fail,
                model,
            ),
            plugins=data_type.format_attr.namespaces,
        )

    def to_data_type(self) -> DataType:
        data_type = None

        element = self.element.to_element()

        format = "; ".join(self.formatters)
        plugins = "; ".join(self.plugins) if self.plugins is not None else None
        format_attr = ValidatorsAttr(format, element, plugins)
        # TODO: Pass tracer here if to_rail is ever used
        format_attr.get_validators(self.element.strict)

        self_is_list = self.element.type == "list"
        children = None
        if self.children:
            children = {}
            child_entries = (
                self.children.get("item", {}) if self_is_list else self.children
            )
            for child_key in child_entries:
                children[child_key] = child_entries[child_key].to_data_type()
            # FIXME: For Lists where the item type is not an object

        if self_is_list:
            # TODO: When to stop this assumption?  What if List[str]?
            object_element = ElementStub("object", {})
            object_format_attr = format_attr
            object_format_attr.element = object_element
            # TODO: Pass tracer here if to_rail is ever used
            object_format_attr.get_validators()
            object_data_type = registry["object"](
                children=children,
                format_attr=object_format_attr,
                element=object_element,
            )
            children = {"item": object_data_type}

        data_type_cls = registry[self.element.type]
        if data_type_cls is not None:
            data_type = data_type_cls(
                children=children, format_attr=format_attr, element=element
            )
            if self.element.type == "date":
                data_type.date_format = (
                    self.element.date_format
                    if self.element.date_format
                    else data_type.date_format
                )
            elif self.element.type == "time":
                data_type.time_format = (
                    self.element.time_format
                    if self.element.time_format
                    else data_type.time_format
                )

        return data_type

    @classmethod
    def from_dict(cls, data_type: dict):
        if data_type is not None:
            children, formatters, element, plugins = pluck(
                data_type, ["children", "formatters", "element", "plugins"]
            )
            children_data_types = None
            if children is not None:
                class_children = {}
                elem_type = element["type"] if element is not None else None
                elem_is_list = elem_type == "list"
                child_entries = children.get("item", {}) if elem_is_list else children
                for child_key in child_entries:
                    class_children[child_key] = cls.from_dict(child_entries[child_key])
                children_data_types = (
                    {"item": class_children} if elem_is_list else class_children
                )
            return cls(
                children_data_types,
                formatters,
                SchemaElementStruct.from_dict(element),
                plugins,
            )

    def to_dict(self):
        response = {
            "formatters": self.formatters,
            "element": self.element.to_dict(),
        }
        if self.children is not None:
            serialized_children = {}
            elem_type = self.element.type if self.element is not None else None
            elem_is_list = elem_type == "list"
            child_entries = (
                self.children.get("item", {}) if elem_is_list else self.children
            )
            for child_key in child_entries:
                serialized_children[child_key] = child_entries[child_key].to_dict()
            response["children"] = (
                {"item": serialized_children} if elem_is_list else serialized_children
            )

        if self.plugins is not None:
            response["plugins"] = self.plugins

        return response

    @classmethod
    def from_request(cls, data_type: dict):
        if data_type:
            children, formatters, element, plugins = pluck(
                data_type, ["children", "formatters", "element", "plugins"]
            )
            children_data_types = None
            if children:
                class_children = {}
                elem_type = element.get("type") if element is not None else None
                elem_is_list = elem_type == "list"
                child_entries = (
                    children.get("item", {}).get("children", {})
                    if elem_is_list
                    else children
                )
                for child_key in child_entries:
                    class_children[child_key] = cls.from_request(
                        child_entries[child_key]
                    )
                children_data_types = (
                    {"item": class_children} if elem_is_list else class_children
                )

            return cls(
                children_data_types,
                formatters,
                SchemaElementStruct.from_request(element),
                plugins,
            )

    def to_response(self):
        response = {
            "formatters": self.formatters,
            "element": self.element.to_response(),
        }
        if self.children is not None:
            serialized_children = {}
            elem_type = self.element.type if self.element is not None else None
            elem_is_list = elem_type == "list"
            child_entries = (
                self.children.get("item", {}) if elem_is_list else self.children
            )
            for child_key in child_entries:
                serialized_children[child_key] = child_entries[child_key].to_response()
            response["children"] = (
                {"item": serialized_children} if elem_is_list else serialized_children
            )

        if self.plugins is not None:
            response["plugins"] = self.plugins

        return response

    @classmethod
    def from_xml(cls, elem: _Element):
        elem_format = elem.get("format", "")
        format_pattern = re.compile(r";(?![^{}]*})")
        format_tokens = re.split(format_pattern, elem_format)
        formatters = list(filter(None, format_tokens))

        element = SchemaElementStruct.from_xml(elem)

        elem_type = elem.tag
        elem_is_list = elem_type == "list"
        children = None
        elem_children = list(elem)  # Not strictly necessary but more readable
        if len(elem_children) > 0:
            if elem_is_list:
                children = {"item": cls.from_xml(elem_children[0]).children}
            else:
                children = {}
                child: _Element
                for child in elem_children:
                    child_key = child.get("name")
                    children[child_key] = cls.from_xml(child)

        elem_plugins = elem.get("plugins", "")
        plugin_pattern = re.compile(r";(?![^{}]*})")
        plugin_tokens = re.split(plugin_pattern, elem_plugins)
        plugins = list(filter(None, plugin_tokens))

        return cls(children, formatters, element, plugins)

    def to_xml(self, parent: _Element, as_parent: Optional[bool] = False) -> _Element:
        element = None
        if as_parent:
            element = parent
            elem_attribs: ElementStub = self.element.to_element()
            for k, v in elem_attribs.attrib.items():
                element.set(k, str(v))
        else:
            element = self.element.to_element()

        format = "; ".join(self.formatters) if len(self.formatters) > 0 else None
        if format is not None:
            element.attrib["format"] = format

        plugins = self.plugins if self.plugins is not None else []
        plugins = "; ".join(plugins) if len(plugins) > 0 else None
        if plugins is not None:
            element.attrib["plugins"] = plugins

        stringified_attribs = {}
        for k, v in element.attrib.items():
            stringified_attribs[k] = str(v)
        xml_data_type = (
            element
            if as_parent
            else SubElement(parent, element.tag, stringified_attribs)
        )

        self_is_list = self.element.type == "list"
        if self.children is not None:
            child_entries: Dict[str, DataTypeStruct] = (
                self.children.get("item", {}) if self_is_list else self.children
            )
            _parent = xml_data_type
            if self_is_list and (
                len(child_entries) > 0 or child_entries[0].element.name is not None
            ):
                _parent = SubElement(xml_data_type, "object")
            for child_key in child_entries:
                child_entries[child_key].to_xml(_parent)

        return xml_data_type

    def get_all_plugins(self) -> List[str]:
        plugins = self.plugins if self.plugins is not None else []

        self_is_list = self.element.type == "list"
        if self.children is not None:
            children = self.children.get("item", {}) if self_is_list else self.children
            for child_key in children:
                plugins.extend(children[child_key].get_all_plugins())
        return plugins

    @staticmethod
    def is_data_type_struct(other: Any) -> bool:
        if isinstance(other, dict):
            data_type_struct_attrs = DataTypeStruct.__dict__.keys()
            other_keys = other.keys()
            return set(other_keys).issubset(data_type_struct_attrs)
        return False
