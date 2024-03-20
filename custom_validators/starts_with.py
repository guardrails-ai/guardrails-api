from typing import Any, Dict, Union, Callable

from guardrails.logger import logger
from guardrails.validator_base import (
    FailResult,
    PassResult,
    ValidationResult,
    Validator,
    register_validator,
)


@register_validator(name="guardrails/starts_with", data_type=["string", "list"])
class StartsWith(Validator):
    """Validates that a list starts with a given value.

    **Key Properties**

    | Property                      | Description                         |
    | ----------------------------- | ---------------------------------   |
    | Name for `format` attribute   | `starts-with`                       |
    | Supported data types          | `string`, `list`                    |
    | Programmatic fix              | Append the given value if absent    |

    Args:
        start: The required last element.
    """

    def __init__(
        self, start: str, on_fail: Union[Callable[..., Any], None] = None, **kwargs
    ):
        super().__init__(on_fail=on_fail, start=start, **kwargs)
        self._start = start

    def validate(self, value: Any, metadata: Dict) -> ValidationResult:
        logger.debug(f"Validating whether {value} starts with {self._start}...")

        if value[0] != self._start:
            return FailResult(
                error_message=f"{value} must start with {self._start}",
                fix_value=(
                    value + [self._start]
                    if isinstance(value, list)
                    else self._start + value
                ),
            )

        return PassResult()