import json
import os
import yaml
import jsonref


def content_type_to_PascalCase(content_type: str) -> str:
    return "".join([w.capitalize() for w in content_type.split("/")])


guardrails_api_spec_file_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../guardrails_api/open-api-spec.json")
)

openai_api_spec_file_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../openai-api-spec.yml")
)

guardrails_api_spec = {}
with open(guardrails_api_spec_file_path, "r+") as guardrails_api_spec_file:
    guardrails_api_spec = json.loads(guardrails_api_spec_file.read())

    with open(openai_api_spec_file_path, "r") as openai_api_spec_file:
        openai_api_spec = yaml.safe_load(openai_api_spec_file.read())

        create_chat_completions_spec = openai_api_spec["paths"]["/chat/completions"][
            "post"
        ]
        create_chat_completions_spec["summary"] = (
            "OpenAI SDK compatible endpoint for Chat Completions"
        )

        derefed_openai_api_spec = jsonref.replace_refs(openai_api_spec)

        create_chat_completions_deref = derefed_openai_api_spec["paths"][
            "/chat/completions"
        ]["post"]  # type: ignore

        ## Request
        request_body_schemas = {}
        request_body_content_spec = create_chat_completions_spec["requestBody"][
            "content"
        ]
        request_body_content = (
            create_chat_completions_deref["requestBody"]["content"] or {}
        )  # type: ignore
        # for content_type in request_body_content:
        for index, (content_type, value) in enumerate(request_body_content.items()):  # type: ignore
            content_type_schema = value["schema"]  # type: ignore
            content_type_schema_ref = request_body_content_spec[content_type]["schema"][
                "$ref"
            ]

            schema_name = ""
            if not content_type_schema_ref:
                postfix = (
                    content_type_to_PascalCase(content_type)
                    if len(request_body_content) > 1
                    else ""
                )
                schema_name = f"CreateChatCompletionRequest{postfix}"
            else:
                schema_name = content_type_schema_ref.split("/")[-1]

            if content_type_schema.get("x-oaiMeta"):
                del content_type_schema["x-oaiMeta"]
            request_body_schemas[schema_name] = jsonref.replace_refs(
                content_type_schema
            )

        ## Responses
        response_body_schemas = {}
        responses_spec = create_chat_completions_spec["responses"]
        derefed_responses = create_chat_completions_deref["responses"] or {}  # type: ignore
        # for content_type in request_body_content:
        for index, (status, value) in enumerate(derefed_responses.items()):  # type: ignore
            for content_type, content_type_value in value["content"].items():
                content_type_schema = content_type_value["schema"]  # type: ignore
                content_type_schema_ref = responses_spec[status]["content"][
                    content_type
                ]["schema"]["$ref"]

                schema_name = ""
                if not content_type_schema_ref:
                    postfix = (
                        content_type_to_PascalCase(content_type)
                        if len(request_body_content) > 1
                        else ""
                    )
                    schema_name = f"CreateChatCompletionResponse{postfix}"
                else:
                    schema_name = content_type_schema_ref.split("/")[-1]

                if content_type_schema.get("x-oaiMeta"):
                    del content_type_schema["x-oaiMeta"]
                response_body_schemas[schema_name] = jsonref.replace_refs(
                    content_type_schema
                )

        ## Replace Custom Spec with Official Spec
        guardrails_chat_completion_spec = guardrails_api_spec["paths"][
            "/guards/{guardName}/openai/v1/chat/completions"
        ]["post"]
        del create_chat_completions_spec["x-oaiMeta"]
        new_create_chat_completions_spec = create_chat_completions_spec
        new_create_chat_completions_spec.update(
            {
                "summary": guardrails_chat_completion_spec["summary"],
                "parameters": guardrails_chat_completion_spec["parameters"],
                "security": guardrails_chat_completion_spec["security"],
            }
        )
        guardrails_api_spec["paths"][
            "/guards/{guardName}/openai/v1/chat/completions"
        ] = {"post": new_create_chat_completions_spec}

        guardrails_api_spec_schemas = guardrails_api_spec["components"]["schemas"]
        del guardrails_api_spec_schemas["OpenAIChatCompletionPayload"]
        del guardrails_api_spec_schemas["OpenAIChatCompletion"]
        new_schemas = {}
        new_schemas.update(guardrails_api_spec_schemas)
        new_schemas.update(request_body_schemas)
        new_schemas.update(response_body_schemas)
        guardrails_api_spec["components"]["schemas"] = new_schemas

with open(guardrails_api_spec_file_path, "w") as guardrails_api_spec_file:
    guardrails_api_spec_file.write(jsonref.dumps(guardrails_api_spec, indent=2))
