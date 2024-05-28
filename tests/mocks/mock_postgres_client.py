from typing import Any, List


class MockSession:
    rows: List[Any]
    queries: List[str]

    def __init__(self) -> None:
        self.rows = []
        self.queries = []
        self.execute_calls = []

    def execute(self, query):
        self.queries.append(query)
        return self

    def all(self):
        return self.rows

    def _set_rows(self, rows: List[Any]):
        self.rows = rows

    def query(self, *args, **kwargs):
        return self

    def filter_by(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self, *args, **kwargs):
        return self

    def add(self, *args, **kwargs):
        return self

    def delete(self, *args, **kwargs):
        return self

    def commit(self, *args, **kwargs):
        return self


class MockDb:
    def __init__(self) -> None:
        self.session = MockSession()


class MockPostgresClient:
    def __init__(self):
        self.db = MockDb()
