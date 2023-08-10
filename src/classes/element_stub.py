from typing import Any, Dict


class ElementStub:
    def __init__(self, tag, attributes: Dict[str, Any]) -> None:
        self.attrib = attributes
        self.tag = tag
