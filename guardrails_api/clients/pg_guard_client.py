from contextlib import contextmanager
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from sqlalchemy.orm import Session
from guardrails_api.classes.http_error import HttpError
from guardrails_api.clients.guard_client import GuardClient
from guardrails_api.db.models.guard_item import GuardItem
from guardrails_api.db.postgres_client import PostgresClient
from guardrails_api.db.models.guard_item_audit import GuardItemAudit
from guardrails_ai.types import CreateGuardRequest, Guard


def from_guard_item(
    guard_item: GuardItem | GuardItemAudit,
) -> Guard:
    guard = Guard.model_validate(guard_item.guard)
    if guard and not guard.id and guard_item.id is not None:
        guard.id = str(guard_item.id)
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

    def util_get_guard_item(self, id: str, db: Session) -> GuardItem | None:
        item = db.query(GuardItem).get(id)
        return item

    def util_create_guard(self, guard: Guard | CreateGuardRequest, db) -> Guard:
        try:
            # Should remove id property from Guard
            guard_req = CreateGuardRequest.model_validate(
                guard.model_dump(exclude_none=True)
            )
            guard_item = GuardItem(
                name=guard.name, guard=guard_req.model_dump(exclude_none=True)
            )
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

    def get_guard(self, id: str, as_of_date: Optional[str] = None) -> Guard:
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
            if audit_item and guard_item:
                guard_item.id = audit_item.guard_id
            if guard_item is None:
                raise HttpError(
                    status=404,
                    message="NotFound",
                    cause="A Guard with the id {id} does not exist!".format(id=id),
                )
            return from_guard_item(guard_item)

    def get_guards(self, guard_name: Optional[str] = None) -> List[Guard]:
        with self.get_db_context() as db:
            guard_items: list[GuardItem] = []
            if guard_name:
                guard_items = db.query(GuardItem).filter_by(name=guard_name).all()
            else:
                guard_items = db.query(GuardItem).all()
            return [from_guard_item(gi) for gi in guard_items]

    def create_guard(self, guard: Guard | CreateGuardRequest) -> Guard:
        with self.get_db_context() as db:
            return self.util_create_guard(guard, db)

    def update_guard(self, id: str, guard: Guard) -> Guard:
        with self.get_db_context() as db:
            guard_item = self.util_get_guard_item(id, db)
            if guard_item is None:
                raise HttpError(
                    status=404,
                    message="NotFound",
                    cause="A Guard with the id {id} does not exist!".format(id=id),
                )
            guard_item.guard = guard.model_dump(exclude_none=True)  # type: ignore - guard_item.guard == JSONB == Column[Any], guard.model_dump() == dict[str, Any]
            guard_item.updated_at = db.execute(  # type: ignore - .scalar() returns datetime or None; either is fine since if None the server will default
                select(func.current_timestamp())
            ).scalar()
            db.commit()
            return from_guard_item(guard_item)

    def upsert_guard(self, id: str, guard: Guard | CreateGuardRequest) -> Guard:
        with self.get_db_context() as db:
            guard_item = self.util_get_guard_item(id, db)
            if guard_item is not None:
                guard_item.guard = guard.model_dump(exclude_none=True)  # type: ignore - guard_item.guard == JSONB == Column[Any], guard.model_dump() == dict[str, Any]
                guard_item.updated_at = db.execute(  # type: ignore - .scalar() returns datetime or None; either is fine since if None the server will default
                    select(func.current_timestamp())
                ).scalar()
                db.commit()
                return from_guard_item(guard_item)
            else:
                return self.util_create_guard(guard, db)

    def delete_guard(self, id: str) -> Guard:
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
