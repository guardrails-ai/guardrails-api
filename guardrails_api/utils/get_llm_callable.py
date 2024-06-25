import litellm
from typing import Any, Awaitable, Callable, Union
from guardrails.utils.openai_utils import (
    get_static_openai_create_func,
    get_static_openai_chat_create_func,
    get_static_openai_acreate_func,
    get_static_openai_chat_acreate_func,
)
from guardrails_api_client.models.llm_resource import LLMResource


def get_llm_callable(
    llm_api: str,
) -> Union[Callable, Callable[[Any], Awaitable[Any]]]:
    # TODO: Add error handling and throw 400
    if llm_api == LLMResource.OPENAI_DOT_COMPLETION_DOT_CREATE.value:
        return get_static_openai_create_func()
    elif llm_api == LLMResource.OPENAI_DOT_CHAT_COMPLETION_DOT_CREATE.value:
        return get_static_openai_chat_create_func()
    elif llm_api == LLMResource.OPENAI_DOT_COMPLETION_DOT_ACREATE.value:
        return get_static_openai_acreate_func()
    elif llm_api == LLMResource.OPENAI_DOT_CHAT_COMPLETION_DOT_ACREATE.value:
        return get_static_openai_chat_acreate_func()
    elif llm_api == LLMResource.LITELLM_DOT_COMPLETION.value:
        return litellm.completion
    elif llm_api == LLMResource.LITELLM_DOT_ACOMPLETION.value:
        return litellm.acompletion
    else:
        pass
