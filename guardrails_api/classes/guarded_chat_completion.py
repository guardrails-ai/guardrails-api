from typing import Optional

from guardrails_ai.types import ValidationOutcome
from litellm import ModelResponse
from pydantic import Field


class GuardedChatCompletion(ModelResponse):
    guardrails: Optional[ValidationOutcome] = Field(default=None)
