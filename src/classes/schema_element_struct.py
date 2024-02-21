from typing import List, Optional
from lxml.etree import _Element
from src.utils.pluck import pluck
from src.classes.element_stub import ElementStub


class SchemaElementStruct:
    def __init__(
        self,
        type: str,
        name: Optional[str],
        description: Optional[str],
        strict: Optional[bool],
        date_format: Optional[str],
        time_format: Optional[str],
        on_fail: Optional[str],
        on_fails: Optional[List[dict]],
        model: Optional[str],
        **kwargs,
    ):
        self.type = type
        self.name = name
        self.description = description
        self.strict = strict
        self.date_format = date_format
        self.time_format = time_format
        self.on_fail = on_fail
        self.on_fails = on_fails if on_fails is not None else []
        self.model = model
        self.attribs = kwargs

    def to_element(self) -> ElementStub:
        elem_dict = self.to_dict()
        if self.date_format is not None:
            elem_dict["date-format"] = self.date_format
        if self.time_format is not None:
            elem_dict["time-format"] = self.time_format
        if self.on_fail is not None:
            elem_dict["on-fail"] = self.on_fail
        if len(self.on_fails) > 0:
            for validator_on_fail in self.on_fails:
                elem_dict[
                    validator_on_fail.get("validatorTag")
                ] = validator_on_fail.get("method")
        elem_dict.pop("date_format", None)
        elem_dict.pop("time_format", None)
        elem_dict.pop("on_fails", None)
        return ElementStub(self.type, elem_dict)

    @classmethod
    def from_dict(cls, schema_element: dict):
        handled_keys = [
            "type",
            "name",
            "description",
            "strict",
            "date_format",
            "time_format",
            "on_fail",
            "on_fails",
            "model",
        ]
        if schema_element is not None:
            (
                type,
                name,
                description,
                strict,
                date_format,
                time_format,
                on_fail,
                on_fails,
                model,
            ) = pluck(schema_element, handled_keys)
            kwargs = {}
            for key in schema_element:
                if key not in handled_keys:
                    kwargs[key] = schema_element[key]
            return cls(
                type,
                name,
                description,
                strict,
                date_format,
                time_format,
                on_fail,
                on_fails,
                model,
                **kwargs,
            )

    def to_dict(self):
        response = {"type": self.type, **self.attribs}

        if self.name is not None:
            response["name"] = self.name
        if self.description is not None:
            response["description"] = self.description
        if self.strict is not None:
            response["strict"] = self.strict
        if self.date_format is not None:
            response["date_format"] = self.date_format
        if self.time_format is not None:
            response["time_format"] = self.time_format
        if self.on_fail is not None:
            response["on_fail"] = self.on_fail
        if len(self.on_fails) > 0:
            response["on_fails"] = self.on_fails
        if self.model is not None:
            response["model"] = self.model

        return response

    @classmethod
    def from_request(cls, schema_element: dict):
        handled_keys = [
            "type",
            "name",
            "description",
            "strict",
            "dateFormat",
            "timeFormat",
            "onFail",
            "onFails",
            "model",
        ]
        if schema_element is not None:
            (
                type,
                name,
                description,
                strict,
                date_format,
                time_format,
                on_fail,
                on_fails,
                model,
            ) = pluck(schema_element, handled_keys)
            kwargs = {}
            for key in schema_element:
                if key not in handled_keys:
                    kwargs[key] = schema_element[key]
            return cls(
                type,
                name,
                description,
                strict,
                date_format,
                time_format,
                on_fail,
                on_fails,
                model,
                **kwargs,
            )

    def to_response(self):
        response = {"type": self.type, **self.attribs}
        if self.name is not None:
            response["name"] = self.name
        if self.description is not None:
            response["description"] = self.description
        if self.strict is not None:
            response["strict"] = self.strict
        if self.date_format is not None:
            response["dateFormat"] = self.date_format
        if self.time_format is not None:
            response["timeFormat"] = self.time_format
        if self.on_fail is not None:
            response["onFail"] = self.on_fail
        if len(self.on_fails) > 0:
            response["onFails"] = self.on_fails
        if self.model is not None:
            response["model"] = self.model

        return response

    @classmethod
    def from_xml(cls, xml: _Element):
        type = xml.tag
        name = xml.get("name")
        description = xml.get("description")
        strict = None
        strict_tag = xml.get("strict")
        if strict_tag:
            strict = True if strict_tag == "true" else False
        date_format = xml.get("date-format")
        time_format = xml.get("time-format")
        on_fail = xml.get("on-fail")
        on_fails = []

        kwargs = {}
        handled_keys = [
            "name",
            "description",
            "strict",
            "date-format",
            "time-format",
            "model",
            "on-fail",
        ]
        attr_keys = xml.keys()
        for attr_key in attr_keys:
            if attr_key.startswith("on-fail") and attr_key != "on-fail":
                on_fail_method = xml.get(attr_key)
                on_fail_tag = attr_key
                print(
                    f"appending to on_fails - ${on_fail_tag} ${on_fail_method}"
                )
                on_fails.append(
                    {"validatorTag": on_fail_tag, "method": on_fail_method}
                )
            elif attr_key not in handled_keys:
                kwargs[attr_key] = xml.get(attr_key)
        model = xml.get("model")
        return cls(
            type,
            name,
            description,
            strict,
            date_format,
            time_format,
            on_fail,
            on_fails,
            model,
            **kwargs,
        )
