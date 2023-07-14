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

class MockDb:
    def __init__(self) -> None:
        self.session = MockSession()

class MockPostgresClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MockPostgresClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.db = MockDb()
        