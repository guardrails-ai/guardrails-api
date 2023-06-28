import os
from guardrails import Guard

class GuardClient:
    def __init__(self):
        self.initialized = True
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, '../../rail-spec.xml')
        self.rail_file = os.path.abspath(filename)
    
    def get_guard(self, guard_id: str):
        return Guard.from_rail(self.rail_file)
        