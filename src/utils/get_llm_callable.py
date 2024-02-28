from typing import Any, Awaitable, Callable, Union
from guardrails.utils.openai_utils import (
    get_static_openai_create_func,
    get_static_openai_chat_create_func,
    get_static_openai_acreate_func,
    get_static_openai_chat_acreate_func
)
from guard_rails_api_client.models.validate_payload_llm_api import (
    ValidatePayloadLlmApi,
)


def get_llm_callable(
    llm_api: str,
) -> Union[Callable, Callable[[Any], Awaitable[Any]]]:
    # TODO: Add error handling and throw 400
    if (
        ValidatePayloadLlmApi(llm_api)
        is ValidatePayloadLlmApi.OPENAI_COMPLETION_CREATE
    ):
        return get_static_openai_create_func()
    elif (
        ValidatePayloadLlmApi(llm_api)
        is ValidatePayloadLlmApi.OPENAI_CHATCOMPLETION_CREATE
    ):
        return get_static_openai_chat_create_func()
    elif (
        ValidatePayloadLlmApi(llm_api)
        is ValidatePayloadLlmApi.OPENAI_COMPLETION_ACREATE
    ):
        return get_static_openai_acreate_func()
    elif (
        ValidatePayloadLlmApi(llm_api)
        is ValidatePayloadLlmApi.OPENAI_CHATCOMPLETION_ACREATE
    ):
        return get_static_openai_chat_acreate_func()
    else:
        pass
