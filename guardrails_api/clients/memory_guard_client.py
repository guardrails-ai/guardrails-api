from typing import Optional, Sequence

from guardrails import AsyncGuard, Guard
from guardrails_api.classes.http_error import HttpError
from guardrails_api.clients.guard_client import GuardClient


class MemoryGuardClient(GuardClient):
    # key value pair of id to guard
    guards: dict[str, Guard | AsyncGuard] = {}

    def __init__(self):
        self.initialized = True

    def get_guard(
        self, id: str, as_of_date: Optional[str] = None
    ) -> Guard | AsyncGuard:
        guard = self.guards.get(id, None)
        if guard is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause="A Guard with the id {id} does not exist!".format(id=id),
            )
        return guard

    def get_guards(  # type: ignore
        self, guard_name: Optional[str] = None
    ) -> Sequence[Guard | AsyncGuard]:
        if guard_name:
            return [g for g in list(self.guards.values()) if g.name == guard_name]
        else:
            return [g for g in list(self.guards.values())]
