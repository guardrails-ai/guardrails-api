from typing import Callable
from unittest.mock import Mock

class MockGuardStruct:
    def to_response(self):
        return { "name": "mock-guard" }

class MockGuardClient:
    def get_guards(self):
        return [MockGuardStruct()]