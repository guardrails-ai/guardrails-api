from src.classes import RailSpecStruct
from src.models import RailspecTemplateItem
from src.utils import pluck


class RailspecTemplateStruct:
    def __init__(
        self, name: str, railspec: RailSpecStruct, owner: str, is_public: bool
    ):
        self.name = name
        self.railspec = railspec
        self.owner = owner
        self.is_public = is_public

    @classmethod
    def from_dict(cls, template: dict):
        name, railspec, owner, is_public = pluck(
            template, ["name", "railspec", "owner", "is_public"]
        )
        return cls(name, RailSpecStruct.from_dict(railspec), owner, is_public)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "railspec": self.railspec.to_dict(),
            "owner": self.owner,
            "is_public": self.is_public,
        }

    @classmethod
    def from_request(cls, template: dict, owner: str):
        name, railspec, is_public = pluck(template, ["name", "railspec", "isPublic"])
        return cls(name, RailSpecStruct.from_request(railspec), owner, is_public)

    def to_response(self) -> dict:
        return {
            "name": self.name,
            "railspec": self.railspec.to_response(),
            "owner": self.owner,
            "isPublic": self.is_public,
        }

    @classmethod
    def from_railspec_template_item(cls, item: RailspecTemplateItem):
        return cls(
            item.name,
            RailSpecStruct.from_dict(item.railspec),
            item.owner,
            item.is_public,
        )
