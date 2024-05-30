import litellm
from typing import Any, Awaitable, Callable, Union
from guardrails.utils.openai_utils import (
    get_static_openai_create_func,
    get_static_openai_chat_create_func,
    get_static_openai_acreate_func,
    get_static_openai_chat_acreate_func,
)
from guardrails_api_client.models.validate_payload_llm_api import (
    ValidatePayloadLlmApi,
)


def get_llm_callable(
    llm_api: str,
) -> Union[Callable, Callable[[Any], Awaitable[Any]]]:
    try:
        model = ValidatePayloadLlmApi(llm_api)
        # TODO: Add error handling and throw 400
        if (
            model is ValidatePayloadLlmApi.OPENAI_COMPLETION_CREATE
            or model is ValidatePayloadLlmApi.OPENAI_COMPLETIONS_CREATE
        ):
            return get_static_openai_create_func()
        elif (
            model is ValidatePayloadLlmApi.OPENAI_CHATCOMPLETION_CREATE
            or model is ValidatePayloadLlmApi.OPENAI_CHAT_COMPLETIONS_CREATE
        ):
            return get_static_openai_chat_create_func()
        elif model is ValidatePayloadLlmApi.OPENAI_COMPLETION_ACREATE:
            return get_static_openai_acreate_func()
        elif model is ValidatePayloadLlmApi.OPENAI_CHATCOMPLETION_ACREATE:
            return get_static_openai_chat_acreate_func()
        elif model is ValidatePayloadLlmApi.LITELLM_COMPLETION:
            return litellm.completion
        elif model is ValidatePayloadLlmApi.LITELLM_ACOMPLETION:
            return litellm.acompletion

        else:
            pass
    except Exception:
        pass
