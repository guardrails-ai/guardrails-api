from guardrails import Guard
from guardrails.classes import ValidationOutcome
from guardrails.classes.validation.validation_summary import (
    ValidationSummary,
    ValidatorLogs,
)


def attach_validation_summaries(
    validation_outcome: ValidationOutcome,
    guard: Guard,
    validator_logs: list[ValidatorLogs] = [],
) -> ValidationOutcome:
    if not validator_logs:
        validator_logs = guard.history.last.validator_logs if guard.history.last else []
    if not validation_outcome.validation_summaries:
        validation_outcome.validation_summaries = (
            ValidationSummary.from_validator_logs_only_fails(validator_logs)
        )
    return validation_outcome
