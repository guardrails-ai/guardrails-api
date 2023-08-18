import yaml
from typing import Dict
from jsonschema import Draft202012Validator
from referencing import Registry, jsonschema as jsonschema_ref

with open("../../open-api-spec.yml", 'r') as open_api_spec:
    api_spec: Dict = yaml.safe_load(open_api_spec)

registry = Registry().with_resources([
    (
        "urn:guardrails-api-spec",
        jsonschema_ref.DRAFT202012.create_resource(api_spec)
    )
])

guard_validator = Draft202012Validator(
    {
        "type": "object",
        "additionalProperties": {"$ref": "urn:guardrails-api-spec#/components/schemas/Guard"},
    },
    registry=registry
)

def validate_payload(payload: dict):
    result = guard_validator.validate(payload)
    print(result)