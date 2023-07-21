from src.classes.rail_spec_struct import RailSpecStruct
from src.models.railspec_template_item import RailspecTemplateItem
from src.utils.pluck import pluck


class RailspecTemplateStruct:
    def __init__(
        self,
        name: str,
        railspec: RailSpecStruct
    ):
        self.name = name
        self.railspec = railspec

    @classmethod
    def from_dict(cls, template: dict):
        name, railspec = pluck(
            template, ["name", "railspec"]
        )
        return cls(name, RailSpecStruct.from_dict(railspec))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "railspec": self.railspec.to_dict()
        }

    @classmethod
    def from_request(cls, template: dict):
        name, railspec = pluck(
            template, ["name", "railspec"]
        )
        return cls(name, RailSpecStruct.from_request(railspec))

    def to_response(self) -> dict:
        return {"name": self.name, "railspec": self.railspec.to_response()}

    @classmethod
    def from_railspec_template_item(cls, item: RailspecTemplateItem):
        return cls(
            item.name,
            RailSpecStruct.from_dict(item.railspec)
        )
