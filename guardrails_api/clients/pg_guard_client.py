from contextlib import contextmanager
from typing import List, Optional
from guardrails_api_client import Guard as GuardStruct
from guardrails_api.classes.http_error import HttpError
from guardrails_api.clients.guard_client import GuardClient
from guardrails_api.models.guard_item import GuardItem
from guardrails_api.clients.postgres_client import PostgresClient
from guardrails_api.models.guard_item_audit import GuardItemAudit


def from_guard_item(guard_item: GuardItem) -> GuardStruct:
    # Temporary fix for the fact that the DB schema is out of date with the API schema
    # For now, we're just storing the serialized guard in the railspec column
    return GuardStruct.from_dict(guard_item.railspec)


class PGGuardClient(GuardClient):
    def __init__(self):
        self.initialized = True
        self.pgClient = PostgresClient()

    @contextmanager
    def get_db_context(self):
        db = self.pgClient.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def util_get_guard_item(self, guard_name: str, db) -> GuardItem:
        item = db.query(GuardItem).filter_by(name=guard_name).first()
        return item


    def util_create_guard(self, guard: GuardStruct, db) -> GuardStruct:
        guard_item = GuardItem(
            name=guard.name,
            railspec=guard.to_dict(),
            num_reasks=None,
            description=guard.description,
        )
        db.add(guard_item)
        db.commit()
        return from_guard_item(guard_item)
    
    # Below are used directly by Controllers and start db sessions

    def get_guard(self, guard_name: str, as_of_date: Optional[str] = None) -> GuardStruct:
        with self.get_db_context() as db:
            latest_guard_item = db.query(GuardItem).filter_by(name=guard_name).first()
            audit_item = None
            if as_of_date is not None:
                audit_item = (
                    db.query(GuardItemAudit)
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
            return from_guard_item(guard_item)

    def get_guards(self) -> List[GuardStruct]:
        with self.get_db_context() as db:
            guard_items = db.query(GuardItem).all()
            return [from_guard_item(gi) for gi in guard_items]
    
    def create_guard(self, guard: GuardStruct) -> GuardStruct:
        with self.get_db_context() as db:
            return self.util_create_guard(guard, db)

    def update_guard(self, guard_name: str, guard: GuardStruct) -> GuardStruct:
        with self.get_db_context() as db:
            guard_item = self.util_get_guard_item(guard_name, db)
            if guard_item is None:
                raise HttpError(
                    status=404,
                    message="NotFound",
                    cause="A Guard with the name {guard_name} does not exist!".format(
                        guard_name=guard_name
                    ),
                )
            # guard_item.num_reasks = guard.num_reasks
            guard_item.railspec = guard.to_dict()
            guard_item.description = guard.description
            db.commit()
            return from_guard_item(guard_item)

    def upsert_guard(self, guard_name: str, guard: GuardStruct) -> GuardStruct:
        with self.get_db_context() as db:
            guard_item = self.util_get_guard_item(guard_name, db)
            if guard_item is not None:
                guard_item.railspec = guard.to_dict()
                guard_item.description = guard.description
                # guard_item.num_reasks = guard.num_reasks
                db.commit()
                return from_guard_item(guard_item)
            else:
                return self.util_create_guard(guard, db)

    def delete_guard(self, guard_name: str) -> GuardStruct:
        with self.get_db_context() as db:
            guard_item = self.util_get_guard_item(guard_name, db)
            if guard_item is None:
                raise HttpError(
                    status=404,
                    message="NotFound",
                    cause="A Guard with the name {guard_name} does not exist!".format(
                        guard_name=guard_name
                    ),
                )
            db.delete(guard_item)
            db.commit()
            guard = from_guard_item(guard_item)
            return guard
