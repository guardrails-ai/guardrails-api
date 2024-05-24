from typing import List
from src.classes.guard_struct import GuardStruct
from src.classes.http_error import HttpError
from src.clients.guard_client import GuardClient
from src.models.guard_item import GuardItem
from src.clients.postgres_client import PostgresClient
from src.models.guard_item_audit import GuardItemAudit


class MemoryGuardClient(GuardClient):
    # key value pair of guard_name to guard_struct
    guards = {}
    def __init__(self):
        self.initialized = True


    def get_guard(self, guard_name: str, as_of_date: str = None) -> GuardStruct:
        # TODO: should this throw if it isn't found?
        guard = self.guards.get(guard_name, None)
        return guard

    def get_guards(self) -> List[GuardStruct]:
        return list(self.guards.values())

    def create_guard(self, guard: GuardStruct) -> GuardStruct:
        self.guards[guard.name] = guard
        return guard 

    def update_guard(self, guard_name: str, new_guard: GuardStruct) -> GuardStruct:
        old_guard = self.get_guard(guard_name)
        if old_guard is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause="A Guard with the name {guard_name} does not exist!".format(
                    guard_name=guard_name
                ),
            )
        old_guard.railspec = new_guard.railspec.to_dict()
        old_guard.num_reasks = new_guard.num_reasks
        self.guards[guard_name] = old_guard
        return old_guard 

    def upsert_guard(self, guard_name: str, new_guard: GuardStruct) -> GuardStruct:
        old_guard = self.get_guard(guard_name)
        if old_guard is not None:
            old_guard.railspec = new_guard.railspec.to_dict()
            old_guard.num_reasks = new_guard.num_reasks
            self.guards[guard_name] = old_guard
            return old_guard 
        else:
            return self.create_guard(new_guard)

    def delete_guard(self, guard_name: str) -> GuardStruct:
        deleted_guard = self.get_guard(guard_name)
        if deleted_guard is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause="A Guard with the name {guard_name} does not exist!".format(
                    guard_name=guard_name
                ),
            )
        del self.guards[guard_name]
        return deleted_guard
