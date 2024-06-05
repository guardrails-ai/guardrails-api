import json
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, jsonschema as jsonschema_ref
from guardrails_api.classes.http_error import HttpError
from guardrails_api.utils.remove_nones import remove_nones

with open("./open-api-spec.json") as api_spec_file:
    api_spec = json.loads(api_spec_file.read())

registry = Registry().with_resources(
    [
        (
            "urn:guardrails-api-spec",
            jsonschema_ref.DRAFT202012.create_resource(api_spec),
        )
    ]
)

guard_validator = Draft202012Validator(
    {
        "$ref": "urn:guardrails-api-spec#/components/schemas/Guard",
    },
    registry=registry,
)


def validate_payload(payload: dict):
    filtered_payload = remove_nones(payload)
    fields = {}
    error: ValidationError
    for error in guard_validator.iter_errors(filtered_payload):
        fields[error.json_path] = fields.get(error.json_path, [])
        fields[error.json_path].append(error.message)

    if fields:
        raise HttpError(
            400,
            "BadRequest",
            "The request payload did not match the required schema.",
            fields,
        )
