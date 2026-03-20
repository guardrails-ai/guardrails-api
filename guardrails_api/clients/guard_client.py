from typing import List, Optional
from guardrails_ai.types import Guard, CreateGuardRequest


class GuardClient:
    def __init__(self):
        self.initialized = True

    def get_guard(self, id: str, as_of_date: Optional[str] = None) -> Guard:
        raise NotImplementedError

    def get_guards(self, guard_name: Optional[str] = None) -> List[Guard]:
        raise NotImplementedError

    def create_guard(self, guard: CreateGuardRequest) -> Guard:
        raise NotImplementedError

    def update_guard(self, id: str, guard: Guard) -> Guard:
        raise NotImplementedError

    def upsert_guard(self, id: str, guard: Guard | CreateGuardRequest) -> Guard:
        raise NotImplementedError

    def delete_guard(self, id: str) -> Guard:
        raise NotImplementedError
