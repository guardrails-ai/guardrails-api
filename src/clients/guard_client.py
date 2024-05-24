from typing import List
from src.classes.guard_struct import GuardStruct
from src.models.guard_item import GuardItem


class GuardClient:
    def __init__(self):
        self.initialized = True
    def get_guard(self, guard_name: str, as_of_date: str = None) -> GuardStruct:
        raise NotImplementedError

    def get_guards(self) -> List[GuardStruct]:
        raise NotImplementedError

    def create_guard(self, guard: GuardStruct) -> GuardStruct:
        raise NotImplementedError

    def update_guard(self, guard_name: str, guard: GuardStruct) -> GuardStruct:
        raise NotImplementedError

    def upsert_guard(self, guard_name: str, guard: GuardStruct) -> GuardStruct:
        raise NotImplementedError

    def delete_guard(self, guard_name: str) -> GuardStruct:
        raise NotImplementedError
