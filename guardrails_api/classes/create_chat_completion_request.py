import sys

from typing import Optional

from openai.types.completion_create_params import CompletionCreateParamsBase

if sys.version_info.minor < 11:
    from typing_extensions import NotRequired
else:
    from typing import NotRequired  # type: ignore


class CreateChatCompletionRequest(CompletionCreateParamsBase):
    stream: NotRequired[Optional[bool]]
