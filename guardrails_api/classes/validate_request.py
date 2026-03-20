import sys

from typing import Any, Optional

from openai.types.completion_create_params import CompletionCreateParamsBase

if sys.version_info.minor < 11:
    from typing_extensions import NotRequired
else:
    from typing import NotRequired  # type: ignore


class ValidateRequest(CompletionCreateParamsBase):
    stream: NotRequired[Optional[bool]]
    llm_api: NotRequired[Optional[str]]
    llm_output: NotRequired[Optional[str]]
    prompt_params: NotRequired[Optional[dict[str, Any]]]
    num_reasks: NotRequired[Optional[int]]
    messages: NotRequired[Optional[list[dict[str, str]]]]
    metadata: NotRequired[Optional[dict[str, Any]]]
    full_schema_reask: NotRequired[Optional[bool]]
    api_key: NotRequired[Optional[str]]
