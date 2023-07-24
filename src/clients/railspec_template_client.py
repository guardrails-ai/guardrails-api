from typing import List
from src.classes import RailspecTemplateStruct, HttpError
from src.models import RailspecTemplateItem
from src.clients import PostgresClient


class RailspecTemplateClient:
    def __init__(self):
        self.initialized = True
        self.pgClient = PostgresClient()

    def _owner_or_public(self, owner: str):
        return (RailspecTemplateItem.owner == owner) | (
            RailspecTemplateItem.is_public is True
        )

    def _get_railspec_template_item(
        self, owner: str, name: str
    ) -> RailspecTemplateItem:
        return (
            self.pgClient.db.session.query(RailspecTemplateItem)
            .filter_by(owner=owner, name=name)
            .first()
        )

    def get_railspec_template(self, owner: str, name: str) -> RailspecTemplateStruct:
        railspec_template_item = (
            self.pgClient.db.session.query(RailspecTemplateItem)
            .filter(self._owner_or_public(owner), name=name)
            .first()
        )
        if railspec_template_item is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause=f"A Railspec Template with the name {name} does not exist!",
            )
        return RailspecTemplateStruct.from_railspec_template_item(
            railspec_template_item
        )

    def get_railspec_templates(self, owner: str) -> List[RailspecTemplateStruct]:
        railspec_template_items = (
            self.pgClient.db.session.query(RailspecTemplateItem)
            .filter_by(self._owner_or_public(owner))
            .all()
        )

        return [
            RailspecTemplateStruct.from_railspec_template_item(gi)
            for gi in railspec_template_items
        ]

    def create_railspec_template(
        self, owner: str, template: RailspecTemplateStruct
    ) -> RailspecTemplateStruct:
        railspec_template_item = RailspecTemplateItem(
            owner=owner,
            name=template.name,
            railspec=template.railspec.to_dict(),
        )
        self.pgClient.db.session.add(railspec_template_item)
        self.pgClient.db.session.commit()
        return RailspecTemplateStruct.from_railspec_template_item(
            railspec_template_item
        )

    def update_railspec_template(
        self, owner: str, name: str, template: RailspecTemplateStruct
    ) -> RailspecTemplateStruct:
        railspec_template_item = self._get_railspec_template_item(owner, name)
        if railspec_template_item is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause=f"A Railspec with the name {name} does not exist!",
            )
        railspec_template_item.railspec = template.railspec.to_dict()
        self.pgClient.db.session.commit()
        return RailspecTemplateStruct.from_railspec_template_item(
            railspec_template_item
        )

    def upsert_railspec_template(
        self, owner: str, name: str, template: RailspecTemplateStruct
    ) -> RailspecTemplateStruct:
        railspec_template_item = self._get_railspec_template_item(owner, name)
        if railspec_template_item is not None:
            railspec_template_item.railspec = template.railspec.to_dict()
            self.pgClient.db.session.commit()
            return RailspecTemplateStruct.from_railspec_template_item(
                railspec_template_item
            )
        else:
            return self.create_railspec_template(template)

    def delete_railspec_template(self, owner: str, name: str) -> RailspecTemplateStruct:
        railspec_template_item = self._get_railspec_template_item(owner, name)
        if railspec_template_item is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause=f"A Railspec with the name {name} does not exist!",
            )
        self.pgClient.db.session.delete(railspec_template_item)
        self.pgClient.db.session.commit()
        template = RailspecTemplateStruct.from_railspec_template_item(
            railspec_template_item
        )
        return template
