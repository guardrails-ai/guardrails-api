import os
import yaml
from typing import Dict
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, jsonschema as jsonschema_ref
from src.classes.http_error import HttpError

with open("./open-api-spec.yml", 'r') as open_api_spec:
    api_spec: Dict = yaml.safe_load(open_api_spec)

registry = Registry().with_resources([
    (
        "urn:guardrails-api-spec",
        jsonschema_ref.DRAFT202012.create_resource(api_spec)
    )
])

guard_validator = Draft202012Validator(
    {
        "$ref": "urn:guardrails-api-spec#/components/schemas/Guard",
    },
    registry=registry
)

def validate_payload(payload: dict):
    fields = {}
    error: ValidationError
    for error in guard_validator.iter_errors(payload):
        fields[error.json_path] = fields.get(error.json_path, [])
        fields[error.json_path].append(error.message)
        
    if fields:
        raise HttpError(
            400,
            "BadRequest",
            "The request payload did not match the required schema.",
            fields
        )