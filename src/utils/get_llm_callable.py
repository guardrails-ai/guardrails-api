import openai
from typing import Any, Awaitable, Callable, Union
from guard_rails_api_client.models.validate_payload_llm_api import (
    ValidatePayloadLlmApi,
)


def get_llm_callable(
    llm_api: str,
) -> Union[Callable, Callable[[Any], Awaitable[Any]]]:
    if ValidatePayloadLlmApi(llm_api) is ValidatePayloadLlmApi.OPENAI_COMPLETION_CREATE:
        return openai.Completion.create
    elif (
        ValidatePayloadLlmApi(llm_api)
        is ValidatePayloadLlmApi.OPENAI_CHATCOMPLETION_CREATE
    ):
        return openai.ChatCompletion.create
    elif (
        ValidatePayloadLlmApi(llm_api)
        is ValidatePayloadLlmApi.OPENAI_COMPLETION_ACREATE
    ):
        return openai.Completion.acreate
    elif (
        ValidatePayloadLlmApi(llm_api)
        is ValidatePayloadLlmApi.OPENAI_CHATCOMPLETION_ACREATE
    ):
        return openai.ChatCompletion.acreate
    else:
        pass
