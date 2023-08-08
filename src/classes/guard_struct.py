from typing import Optional
from guardrails import Guard, Rail
from src.classes.rail_spec_struct import RailSpecStruct
from src.models.guard_item import GuardItem
from src.utils.pluck import pluck


class GuardStruct:
    def __init__(
        self,
        name: str,
        railspec: RailSpecStruct,
        num_reasks: int = None,
        description: str = None
        # base_model: dict = None,
    ):
        self.name = name
        self.railspec = railspec
        self.num_reasks = num_reasks
        self.description = description
        # self.base_model = base_model

    @classmethod
    def from_guard(cls, guard: Guard):
        return cls(
            "guard-1", RailSpecStruct.from_rail(guard.rail), guard.num_reasks, guard.description
        )

    def to_guard(self, openai_api_key: Optional[str] = None) -> Guard:
        rail_xml = self.railspec.to_xml()
        return Guard(
            Rail.from_xml(rail_xml),
            self.num_reasks,
            openai_api_key=openai_api_key,
            description=self.description,
            name=self.name
        )

    @classmethod
    def from_dict(cls, guard: dict):
        name, railspec, num_reasks, description = pluck(
            guard, ["name", "railspec", "num_reasks", "description"]
        )
        return cls(name, RailSpecStruct.from_dict(railspec), num_reasks, description)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "railspec": self.railspec.to_dict(),
            "num_reasks": self.num_reasks,
            "description": self.description
        }

    @classmethod
    def from_request(cls, guard: dict):
        name, railspec, num_reasks, description = pluck(
            guard, ["name", "railspec", "numReasks", description]
        )
        return cls(name, RailSpecStruct.from_request(railspec), num_reasks, description)

    def to_response(self) -> dict:
        response = {"name": self.name, "railspec": self.railspec.to_response()}
        if self.num_reasks is not None:
            response["numReasks"] = self.num_reasks
        if self.description is not None:
            response["description"] = self.description
        return response

    @classmethod
    def from_guard_item(cls, guard_item: GuardItem):
        return cls(
            guard_item.name,
            RailSpecStruct.from_dict(guard_item.railspec),
            guard_item.num_reasks,
            guard_item.description
        )

    @classmethod
    def from_railspec(cls, name: str, railspec: str, num_reasks: int = None, description: str = None):
        return cls(name, RailSpecStruct.from_xml(railspec), num_reasks, description)
