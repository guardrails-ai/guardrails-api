from typing import List
from src.classes.guard_struct import GuardStruct
from src.classes.http_error import HttpError
from src.models.guard_item import GuardItem
from src.clients.postgres_client import PostgresClient
from src.models.guard_item_audit import GuardItemAudit


class GuardClient:
    def __init__(self):
        self.initialized = True
        self.pgClient = PostgresClient()

    def get_guard(self, guard_name: str, as_of_date: str = None) -> GuardStruct:
        latest_guard_item = (
            self.pgClient.db.session.query(GuardItem)
            .filter_by(name=guard_name)
            .first()
        )
        audit_item = None
        if as_of_date is not None:
            audit_item = (
                self.pgClient.db.session.query(GuardItemAudit)
                .filter_by(name=guard_name)
                .filter(GuardItemAudit.replaced_on > as_of_date)
                .order_by(GuardItemAudit.replaced_on.asc())
                .first()
            )
        guard_item = audit_item if audit_item is not None else latest_guard_item
        if guard_item is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause="A Guard with the name {guard_name} does not exist!".format(
                    guard_name=guard_name
                ),
            )
        return GuardStruct.from_guard_item(guard_item)

    def get_guard_item(self, guard_name: str) -> GuardItem:
        return (
            self.pgClient.db.session.query(GuardItem)
            .filter_by(name=guard_name)
            .first()
        )

    def get_guards(self) -> List[GuardStruct]:
        guard_items = self.pgClient.db.session.query(GuardItem).all()

        return [GuardStruct.from_guard_item(gi) for gi in guard_items]

    def create_guard(self, guard: GuardStruct) -> GuardStruct:
        guard_item = GuardItem(
            name=guard.name,
            railspec=guard.railspec.to_dict(),
            num_reasks=guard.num_reasks,
            description=guard.description,
        )
        self.pgClient.db.session.add(guard_item)
        self.pgClient.db.session.commit()
        return GuardStruct.from_guard_item(guard_item)

    def update_guard(self, guard_name: str, guard: GuardStruct) -> GuardStruct:
        guard_item = self.get_guard_item(guard_name)
        if guard_item is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause="A Guard with the name {guard_name} does not exist!".format(
                    guard_name=guard_name
                ),
            )
        guard_item.railspec = guard.railspec.to_dict()
        guard_item.num_reasks = guard.num_reasks
        self.pgClient.db.session.commit()
        return GuardStruct.from_guard_item(guard_item)

    def upsert_guard(self, guard_name: str, guard: GuardStruct) -> GuardStruct:
        guard_item = self.get_guard_item(guard_name)
        if guard_item is not None:
            guard_item.railspec = guard.railspec.to_dict()
            guard_item.num_reasks = guard.num_reasks
            self.pgClient.db.session.commit()
            return GuardStruct.from_guard_item(guard_item)
        else:
            return self.create_guard(guard)

    def delete_guard(self, guard_name: str) -> GuardStruct:
        guard_item = self.get_guard_item(guard_name)
        if guard_item is None:
            raise HttpError(
                status=404,
                message="NotFound",
                cause="A Guard with the name {guard_name} does not exist!".format(
                    guard_name=guard_name
                ),
            )
        self.pgClient.db.session.delete(guard_item)
        self.pgClient.db.session.commit()
        guard = GuardStruct.from_guard_item(guard_item)
        return guard
