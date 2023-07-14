from typing import List


class MockBlueprint:
    name: str
    module_name: str
    routes: List[str]
    def __init__(self, name: str, module_name: str, **kwargs):
        self.name = name
        self.module_name = module_name
        self.routes = []
        for key in kwargs:
            self[key] = kwargs.get("key")

    def route(self, route_name: str):
        self.routes.append(route_name)

        