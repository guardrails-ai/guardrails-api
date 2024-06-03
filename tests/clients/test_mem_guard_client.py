import pytest
from unittest.mock import ANY as AnyMatcher
from src.classes.http_error import HttpError

# from src.clients.memory_guard_client import MemoryGuardClient
from src.models.guard_item import GuardItem
from src.models.guard_item_audit import GuardItemAudit
from tests.mocks.mock_postgres_client import MockPostgresClient
from tests.mocks.mock_guard_client import MockGuardStruct, MockRailspec
from unittest.mock import call


def test_init(mocker):
    from src.clients.memory_guard_client import MemoryGuardClient

    mem_guard_client = MemoryGuardClient()

    assert mem_guard_client.initialized is True


class TestGetGuard:
    def test_get_all(self, mocker):
        from src.clients.memory_guard_client import MemoryGuardClient
        

        guard_client = MemoryGuardClient()

        result = guard_client.get_guards()

        assert result == []
    def test_get_all_after_insert(self, mocker):
        from src.clients.memory_guard_client import MemoryGuardClient
        

        guard_client = MemoryGuardClient()
        new_guard = MockGuardStruct()
        guard_client.create_guard(new_guard)
        result = guard_client.get_guards()

        assert result == [new_guard]

    def test_get_guard_after_insert(self, mocker):
        from src.clients.memory_guard_client import MemoryGuardClient
        

        guard_client = MemoryGuardClient()
        new_guard = MockGuardStruct('test_guard')
        guard_client.create_guard(new_guard)
        result = guard_client.get_guard('test_guard')

        assert result == new_guard

    def test_not_found(self, mocker):
        from src.clients.memory_guard_client import MemoryGuardClient
        

        guard_client = MemoryGuardClient()
        new_guard = MockGuardStruct('test_guard')
        guard_client.create_guard(new_guard)
        result = guard_client.get_guard('guard_that_does_not_exist')
        
        assert result is None













