from typing import Optional, Sequence

from guardrails import Guard
from guardrails_api.classes.http_error import HttpError
from guardrails_api.clients.guard_client import GuardClient


class MemoryGuardClient(GuardClient):
    # key value pair of id to guard
    guards: dict[str, Guard] = {}

    def __init__(self):
        self.initialized = True

    def get_guard(self, id: str, as_of_date: Optional[str] = None) -> Guard | None:
        guard = self.guards.get(id, None)
        if guard is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause="A Guard with the id {id} does not exist!".format(id=id),
            )
        return guard

    def get_guards(self, guard_name: Optional[str] = None) -> Sequence[Guard]:
        if guard_name:
            return [g for g in list(self.guards.values()) if g.name == guard_name]
        else:
            return [g for g in list(self.guards.values())]

    def create_guard(self, guard: Guard) -> Guard:
        self.guards[guard.id] = guard
        return guard

    def update_guard(self, id: str, guard: Guard) -> Guard:
        old_guard = self.get_guard(id)
        if old_guard is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause="A Guard with the id {id} does not exist!".format(id=id),
            )
        self.guards[id] = guard
        return guard

    def upsert_guard(self, id: str, guard: Guard) -> Guard:
        self.guards[id] = guard
        return guard

    def delete_guard(self, id: str) -> Guard:
        deleted_guard = self.get_guard(id)
        if deleted_guard is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause="A Guard with the id {id} does not exist!".format(id=id),
            )
        del self.guards[id]
        return deleted_guard
