from contextlib import contextmanager
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from guardrails_api_client import Guard as GuardStruct
from sqlalchemy.orm import Session
from guardrails_api.classes.http_error import HttpError
from guardrails_api.clients.guard_client import GuardClient
from guardrails_api.db.models.guard_item import GuardItem
from guardrails_api.db.postgres_client import PostgresClient
from guardrails_api.db.models.guard_item_audit import GuardItemAudit


def from_guard_item(
    guard_item: GuardItem | GuardItemAudit | None,
) -> GuardStruct | None:
    if not guard_item:
        return guard_item
    guard = GuardStruct.from_dict(guard_item.guard)  # type: ignore
    if guard and guard_item.id:  # type: ignore
        guard.id = guard_item.id  # type: ignore
    return guard


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

    # These are only internal utilities and do not start db sessions

    def util_get_guard_item(self, id: str, db: Session) -> GuardItem:
        item = db.query(GuardItem).get(id)
        return item

    def util_create_guard(self, guard: GuardStruct, db) -> GuardStruct:
        try:
            guard_item = GuardItem(name=guard.name, guard=guard.to_dict())
            db.add(guard_item)
            db.commit()
            return from_guard_item(guard_item)
        except IntegrityError as ie:
            if isinstance(ie.orig, UniqueViolation):
                raise HttpError(
                    status=409,
                    message="Conflict",
                    cause=f"A Guard with the name {guard.name} already exists!",
                )
            raise ie

    # Below are used directly by Controllers and start db sessions

    def get_guard(self, id: str, as_of_date: Optional[str] = None) -> GuardStruct:
        with self.get_db_context() as db:
            latest_guard_item = db.query(GuardItem).get(id)
            audit_item = None
            if as_of_date is not None:
                audit_item = (
                    db.query(GuardItemAudit)
                    .filter_by(guard_id=id)
                    .filter(GuardItemAudit.replaced_on > as_of_date)
                    .order_by(GuardItemAudit.replaced_on.asc())
                    .first()
                )
            guard_item = audit_item if audit_item is not None else latest_guard_item
            if audit_item:
                guard_item = audit_item.guard_id
            if guard_item is None:
                raise HttpError(
                    status=404,
                    message="NotFound",
                    cause="A Guard with the id {id} does not exist!".format(id=id),
                )
            return from_guard_item(guard_item)

    def get_guards(self, guard_name: Optional[str] = None) -> List[GuardStruct]:
        with self.get_db_context() as db:
            guard_items = []
            if guard_name:
                guard_items = db.query(GuardItem).filter_by(name=guard_name).all()
            else:
                guard_items = db.query(GuardItem).all()
            return [from_guard_item(gi) for gi in guard_items]

    def create_guard(self, guard: GuardStruct) -> GuardStruct:
        with self.get_db_context() as db:
            return self.util_create_guard(guard, db)

    def update_guard(self, id: str, guard: GuardStruct) -> GuardStruct:
        with self.get_db_context() as db:
            guard_item = self.util_get_guard_item(id, db)
            if guard_item is None:
                raise HttpError(
                    status=404,
                    message="NotFound",
                    cause="A Guard with the id {id} does not exist!".format(id=id),
                )
            guard_item.guard = guard.to_dict()
            guard_item.updated_at = db.execute(
                select(func.current_timestamp())
            ).scalar()
            db.commit()
            return from_guard_item(guard_item)

    def upsert_guard(self, id: str, guard: GuardStruct) -> GuardStruct:
        with self.get_db_context() as db:
            guard_item = self.util_get_guard_item(id, db)
            if guard_item is not None:
                guard_item.guard = guard.to_dict()
                guard_item.updated_at = db.execute(
                    select(func.current_timestamp())
                ).scalar()
                db.commit()
                return from_guard_item(guard_item)
            else:
                return self.util_create_guard(guard, db)

    def delete_guard(self, id: str) -> GuardStruct:
        with self.get_db_context() as db:
            guard_item = self.util_get_guard_item(id, db)
            if guard_item is None:
                raise HttpError(
                    status=404,
                    message="NotFound",
                    cause="A Guard with the id {id} does not exist!".format(id=id),
                )
            db.delete(guard_item)
            db.commit()
            guard = from_guard_item(guard_item)
            return guard
