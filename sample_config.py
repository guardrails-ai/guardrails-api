"""
All guards defined here will be initialized, if and only if
the application is using in memory guards.

The application will use in memory guards if pg_host is left
undefined. Otherwise, a postgres instance will be started
and guards will be persisted into postgres. In that case,
these guards will not be initialized.
"""

from guardrails import Guard, OnFailAction
from guardrails.hub import (
    DetectPII,
    CompetitorCheck,
    RegexMatch
)


name_case = Guard(
    name='name-case',
    description='Checks that a string is in Title Case format.'
).use(
    RegexMatch(regex="^(?:[A-Z][^\\s]*\\s?)+$")
)

no_guards = Guard()
no_guards.name = "No Guards"

output_guard = Guard()
output_guard.name = "Output Guard"
output_guard.use_many(
    DetectPII(
        pii_entities='pii',
        on_fail=OnFailAction.FIX
    ),
    CompetitorCheck(
        competitors=['OpenAI', 'Anthropic'],
        on_fail=OnFailAction.FIX
    )
)

