class MockRailspec:
    def to_dict(self, *args, **kwargs):
        return {}

class MockGuardStruct:
    name: str
    description: str
    num_reasks: int
    history = []
    
    def __init__(
        self,
        name: str = "mock-guard",
        num_reasks: str = 0,
        description: str = "mock guard description",
        railspec = {}
    ):
        self.name = name
        self.description = description
        self.num_reasks = num_reasks
        self.railspec = MockRailspec()
    
    def to_response(self):
        return { "name": "mock-guard" }

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