import litellm
from typing import Any, Awaitable, Callable, Union
from guardrails.utils.openai_utils import (
    get_static_openai_create_func,
    get_static_openai_chat_create_func,
    get_static_openai_acreate_func,
    get_static_openai_chat_acreate_func,
)
from guardrails_api_client.models.validate_payload import (
    ValidatePayload,
)
from guardrails_api_client.models.llm_resource import ( LLMResource )


def get_llm_callable(
    llm_api: str,
) -> Union[Callable, Callable[[Any], Awaitable[Any]]]:
    try:
        model = ValidatePayload(llm_api)
        # TODO: Add error handling and throw 400
        if (
            model is LLMResource.OPENAI_DOT_COMPLETION_DOT_CREATE
        ):
            return get_static_openai_create_func()
        elif (
            model is LLMResource.OPENAI_DOT_CHAT_COMPLETION_DOT_CREATE
        ):
            return get_static_openai_chat_create_func()
        elif model is LLMResource.OPENAI_DOT_COMPLETION_DOT_ACREATE:
            return get_static_openai_acreate_func()
        elif model is LLMResource.OPENAI_DOT_CHAT_COMPLETION_DOT_ACREATE:
            return get_static_openai_chat_acreate_func()
        elif model is LLMResource.LITELLM_DOT_COMPLETION:
            return litellm.completion
        elif model is LLMResource.LITELLM_DOT_ACOMPLETION:
            return litellm.acompletion

        else:
            pass
    except Exception:
        pass
