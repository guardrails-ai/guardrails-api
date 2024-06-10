from typing import Any, List
from guardrails_api_client import Guard as GuardStruct


class MockGuardStruct(GuardStruct):
    id:str = 'mock-guard-id'
    name: str = "mock-guard"
    description: str = "mock guard description"
    history:List[Any] = []


    def to_guard(self, *args):
        return self

    def parse(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        pass


class MockGuardClient:
    def get_guards(self):
        return [MockGuardStruct()]

    def create_guard(self, guard: MockGuardStruct):
        return MockGuardStruct()
