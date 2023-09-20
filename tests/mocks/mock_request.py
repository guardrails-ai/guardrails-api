class MockRequest:
    method: str

    def __init__(self, method: str):
        self.method = method