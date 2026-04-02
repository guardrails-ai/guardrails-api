import sys

from typing import Any, Optional

from openai.types.chat.completion_create_params import (
    CompletionCreateParamsBase,
    Function,
)
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_union_param import (
    ChatCompletionToolUnionParam,
)

if sys.version_info.minor < 11:
    from typing_extensions import NotRequired
else:
    from typing import NotRequired  # type: ignore


class ValidateRequest(CompletionCreateParamsBase):
    # Overrides
    stream: NotRequired[Optional[bool]]
    model: NotRequired[Optional[str]]  # type: ignore
    # NOTE: The OpenAI sdk has the below fields typed as "Iterable[x]" which isn't supported in Pydantic
    # See: https://github.com/pydantic/pydantic/issues/9541
    # And: https://github.com/pydantic/pydantic-core/pull/1792
    messages: NotRequired[Optional[list[ChatCompletionMessageParam]]]  # type: ignore
    tools: NotRequired[list[ChatCompletionToolUnionParam]]  # type: ignore
    functions: NotRequired[list[Function]]  # type: ignore

    # Guardrails AI specific fields
    llm_api: NotRequired[Optional[str]]
    llm_output: NotRequired[Optional[str]]
    prompt_params: NotRequired[Optional[dict[str, Any]]]
    num_reasks: NotRequired[Optional[int]]
    metadata: NotRequired[Optional[dict[str, Any]]]
    full_schema_reask: NotRequired[Optional[bool]]
    api_key: NotRequired[Optional[str]]
