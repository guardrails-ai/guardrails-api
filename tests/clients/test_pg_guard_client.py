"""Unit tests for guardrails_api.clients.pg_guard_client module."""

import unittest
from unittest.mock import Mock, patch, ANY
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from guardrails_api.classes.http_error import HttpError
from guardrails_api.clients.pg_guard_client import PGGuardClient, from_guard_item


class _ComparableMock(Mock):
    """Mock subclass that supports rich comparison operators (e.g. for SQLAlchemy columns)."""

    def __gt__(self, other):  # noqa: ARG002
        return Mock()


class TestFromGuardItem(unittest.TestCase):
    """Test cases for the from_guard_item function."""

    def test_from_guard_item_sets_id_when_present(self):
        """Test that guard.id is set from guard_item.id when both exist."""
        guard_data = {"name": "test"}
        guard_item = Mock()
        guard_item.guard = guard_data
        guard_item.id = "some-uuid"

        result = from_guard_item(guard_item)

        self.assertEqual(result.id, "some-uuid")

    def test_from_guard_item_no_id_on_guard_item(self):
        """Test that ValidationError is raised if guard.id is not set when guard_item.id is falsy."""
        guard_data = {"name": "test"}
        guard_item = Mock()
        guard_item.guard = guard_data
        guard_item.id = None

        with self.assertRaises(ValidationError):
            from_guard_item(guard_item)


class TestPGGuardClientInit(unittest.TestCase):
    """Test cases for PGGuardClient initialization."""

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_initialization_sets_initialized(self, mock_pg_client):
        """Test PGGuardClient sets initialized to True."""
        client = PGGuardClient()
        self.assertTrue(client.initialized)

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_initialization_creates_pg_client(self, mock_pg_client):
        """Test PGGuardClient creates a PostgresClient instance."""
        mock_instance = Mock()
        mock_pg_client.return_value = mock_instance

        client = PGGuardClient()

        mock_pg_client.assert_called_once()
        self.assertEqual(client.pgClient, mock_instance)


class TestGetDbContext(unittest.TestCase):
    """Test cases for PGGuardClient.get_db_context."""

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_yields_session(self, mock_pg_client):
        """Test that get_db_context yields the db session."""
        mock_session = Mock()
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        client = PGGuardClient()
        with client.get_db_context() as db:
            self.assertEqual(db, mock_session)

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_closes_session_on_exit(self, mock_pg_client):
        """Test that get_db_context closes the session on normal exit."""
        mock_session = Mock()
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        client = PGGuardClient()
        with client.get_db_context():
            pass

        mock_session.close.assert_called_once()

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_closes_session_on_exception(self, mock_pg_client):
        """Test that get_db_context closes the session even when an exception occurs."""
        mock_session = Mock()
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        client = PGGuardClient()
        with self.assertRaises(RuntimeError):
            with client.get_db_context():
                raise RuntimeError("boom")

        mock_session.close.assert_called_once()


class TestUtilGetGuardItem(unittest.TestCase):
    """Test cases for PGGuardClient.util_get_guard_item."""

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_returns_guard_item_from_db(self, mock_pg_client):
        """Test that util_get_guard_item queries by id and returns the result."""
        mock_guard_item = Mock()
        mock_db = Mock()
        mock_db.query.return_value.get.return_value = mock_guard_item

        client = PGGuardClient()
        result = client.util_get_guard_item("some-id", mock_db)

        self.assertEqual(result, mock_guard_item)

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_returns_none_when_not_found(self, mock_pg_client):
        """Test that util_get_guard_item returns None when no item found."""
        mock_db = Mock()
        mock_db.query.return_value.get.return_value = None

        client = PGGuardClient()
        result = client.util_get_guard_item("missing-id", mock_db)

        self.assertIsNone(result)

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_queries_guard_item_model(self, mock_pg_client):
        """Test that util_get_guard_item queries the GuardItem model."""
        from guardrails_api.db.models.guard_item import GuardItem

        mock_db = Mock()
        mock_db.query.return_value.get.return_value = None

        client = PGGuardClient()
        client.util_get_guard_item("some-id", mock_db)

        mock_db.query.assert_called_once_with(GuardItem)
        mock_db.query.return_value.get.assert_called_once_with("some-id")


class TestUtilCreateGuard(unittest.TestCase):
    """Test cases for PGGuardClient.util_create_guard."""

    @patch("guardrails_api.clients.pg_guard_client.from_guard_item")
    @patch("guardrails_api.clients.pg_guard_client.GuardItem")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_creates_and_commits_guard(
        self, mock_pg_client, mock_guard_item_class, mock_from_guard_item
    ):
        """Test util_create_guard adds guard item and commits."""
        mock_db = Mock()
        mock_guard = Mock()
        mock_guard.name = "test_guard"
        mock_guard.model_dump.return_value = {"name": "test_guard"}

        mock_guard_item = Mock()
        mock_guard_item_class.return_value = mock_guard_item
        mock_result = Mock()
        mock_from_guard_item.return_value = mock_result

        client = PGGuardClient()
        result = client.util_create_guard(mock_guard, mock_db)

        mock_guard_item_class.assert_called_once_with(
            id=ANY, name="test_guard", guard={"name": "test_guard"}
        )
        mock_db.add.assert_called_once_with(mock_guard_item)
        mock_db.commit.assert_called_once()
        mock_from_guard_item.assert_called_once_with(mock_guard_item)
        self.assertEqual(result, mock_result)

    @patch("guardrails_api.clients.pg_guard_client.GuardItem")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_raises_http_409_on_unique_violation(
        self, mock_pg_client, mock_guard_item_class
    ):
        """Test util_create_guard raises HttpError 409 on UniqueViolation."""
        mock_db = Mock()
        mock_guard = Mock()
        mock_guard.name = "duplicate_guard"
        mock_guard.model_dump.return_value = {"name": "duplicate_guard"}

        unique_violation = UniqueViolation()
        integrity_error = IntegrityError(
            statement=None, params=None, orig=unique_violation
        )
        mock_db.add.side_effect = integrity_error

        client = PGGuardClient()
        with self.assertRaises(HttpError) as ctx:
            client.util_create_guard(mock_guard, mock_db)

        error = ctx.exception
        self.assertEqual(error.status, 409)
        self.assertEqual(error.message, "Conflict")
        self.assertIsNotNone(error.cause)
        self.assertIn("duplicate_guard", error.cause)  # type: ignore[arg-type]

    @patch("guardrails_api.clients.pg_guard_client.GuardItem")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_reraises_non_unique_integrity_error(
        self, mock_pg_client, mock_guard_item_class
    ):
        """Test util_create_guard re-raises IntegrityError that is not UniqueViolation."""
        mock_db = Mock()
        mock_guard = Mock()
        mock_guard.name = "test_guard"
        mock_guard.model_dump.return_value = {}

        other_error = IntegrityError(
            statement=None, params=None, orig=Exception("other")
        )
        mock_db.add.side_effect = other_error

        client = PGGuardClient()
        with self.assertRaises(IntegrityError):
            client.util_create_guard(mock_guard, mock_db)


class TestGetGuard(unittest.TestCase):
    """Test cases for PGGuardClient.get_guard."""

    @patch("guardrails_api.clients.pg_guard_client.from_guard_item")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_returns_latest_guard_without_as_of_date(
        self, mock_pg_client, mock_from_guard_item
    ):
        """Test get_guard returns the latest guard when no as_of_date given."""
        mock_guard_item = Mock()
        mock_session = Mock()
        mock_session.query.return_value.get.return_value = mock_guard_item
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        mock_result = Mock()
        mock_from_guard_item.return_value = mock_result

        client = PGGuardClient()
        result = client.get_guard("some-id")

        mock_from_guard_item.assert_called_once_with(mock_guard_item)
        self.assertEqual(result, mock_result)

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_raises_404_when_guard_not_found(self, mock_pg_client):
        """Test get_guard raises HttpError 404 when guard does not exist."""
        mock_session = Mock()
        mock_session.query.return_value.get.return_value = None
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        client = PGGuardClient()
        with self.assertRaises(HttpError) as ctx:
            client.get_guard("missing-id")

        error = ctx.exception
        self.assertEqual(error.status, 404)
        self.assertEqual(error.message, "NotFound")
        self.assertIsNotNone(error.cause)
        self.assertIn("missing-id", error.cause)  # type: ignore[arg-type]

    @patch("guardrails_api.clients.pg_guard_client.from_guard_item")
    @patch("guardrails_api.clients.pg_guard_client.GuardItemAudit")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_returns_audit_guard_id_when_as_of_date_given(
        self, mock_pg_client, mock_audit_class, mock_from_guard_item
    ):
        """Test get_guard uses audit item's guard_id when as_of_date is provided."""
        mock_audit_class.replaced_on = _ComparableMock()
        mock_latest = Mock()
        mock_latest = "guard-id"
        mock_audit_item = Mock()
        mock_audit_item.id = "audit-id"
        mock_audit_item.guard_id = "guard-id"

        mock_session = Mock()
        mock_session.query.return_value.get.return_value = mock_latest
        (
            mock_session.query.return_value.filter_by.return_value.filter.return_value.order_by.return_value.first.return_value
        ) = mock_audit_item
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        mock_result = Mock()
        mock_from_guard_item.return_value = mock_result

        client = PGGuardClient()
        client.get_guard("some-id", as_of_date="2024-01-01")

        guard_item = mock_from_guard_item.call_args[0][0]
        self.assertEqual(guard_item.id, "guard-id")

    @patch("guardrails_api.clients.pg_guard_client.from_guard_item")
    @patch("guardrails_api.clients.pg_guard_client.GuardItemAudit")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_falls_back_to_latest_when_no_audit_found(
        self, mock_pg_client, mock_audit_class, mock_from_guard_item
    ):
        """Test get_guard falls back to latest guard when audit query returns None."""
        mock_audit_class.replaced_on = _ComparableMock()
        mock_latest = Mock()

        mock_session = Mock()
        mock_session.query.return_value.get.return_value = mock_latest
        (
            mock_session.query.return_value.filter_by.return_value.filter.return_value.order_by.return_value.first.return_value
        ) = None
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        mock_result = Mock()
        mock_from_guard_item.return_value = mock_result

        client = PGGuardClient()
        result = client.get_guard("some-id", as_of_date="2024-01-01")

        mock_from_guard_item.assert_called_once_with(mock_latest)
        self.assertEqual(result, mock_result)


class TestGetGuards(unittest.TestCase):
    """Test cases for PGGuardClient.get_guards."""

    @patch("guardrails_api.clients.pg_guard_client.from_guard_item")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_returns_all_guards_when_no_filter(
        self, mock_pg_client, mock_from_guard_item
    ):
        """Test get_guards returns all guards when no guard_name is given."""
        mock_item1 = Mock()
        mock_item2 = Mock()
        mock_session = Mock()
        mock_session.query.return_value.all.return_value = [mock_item1, mock_item2]
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        mock_guard1, mock_guard2 = Mock(), Mock()
        mock_from_guard_item.side_effect = [mock_guard1, mock_guard2]

        client = PGGuardClient()
        result = client.get_guards()

        self.assertEqual(result, [mock_guard1, mock_guard2])
        mock_session.query.return_value.all.assert_called_once()

    @patch("guardrails_api.clients.pg_guard_client.from_guard_item")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_filters_by_name_when_provided(self, mock_pg_client, mock_from_guard_item):
        """Test get_guards filters by guard_name when provided."""
        mock_item = Mock()
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.all.return_value = [
            mock_item
        ]
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        mock_guard = Mock()
        mock_from_guard_item.return_value = mock_guard

        client = PGGuardClient()
        result = client.get_guards(guard_name="my_guard")

        mock_session.query.return_value.filter_by.assert_called_once_with(
            name="my_guard"
        )
        self.assertEqual(result, [mock_guard])

    @patch("guardrails_api.clients.pg_guard_client.from_guard_item")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_returns_empty_list_when_no_guards(
        self, mock_pg_client, mock_from_guard_item
    ):
        """Test get_guards returns empty list when no guards exist."""
        mock_session = Mock()
        mock_session.query.return_value.all.return_value = []
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        client = PGGuardClient()
        result = client.get_guards()

        self.assertEqual(result, [])


class TestCreateGuard(unittest.TestCase):
    """Test cases for PGGuardClient.create_guard."""

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_delegates_to_util_create_guard(self, mock_pg_client):
        """Test create_guard calls util_create_guard with the guard and db session."""
        mock_session = Mock()
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        mock_guard = Mock()
        mock_result = Mock()

        client = PGGuardClient()
        client.util_create_guard = Mock(return_value=mock_result)

        result = client.create_guard(mock_guard)

        client.util_create_guard.assert_called_once_with(mock_guard, mock_session)
        self.assertEqual(result, mock_result)


class TestUpdateGuard(unittest.TestCase):
    """Test cases for PGGuardClient.update_guard."""

    @patch("guardrails_api.clients.pg_guard_client.from_guard_item")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_updates_existing_guard(self, mock_pg_client, mock_from_guard_item):
        """Test update_guard updates the guard dict, timestamps, and commits."""
        mock_guard_item = Mock()
        mock_session = Mock()
        mock_session.execute.return_value.scalar.return_value = "2024-01-01T00:00:00"
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        mock_guard = Mock()
        mock_guard.model_dump.return_value = {"name": "updated"}
        mock_result = Mock()
        mock_from_guard_item.return_value = mock_result

        client = PGGuardClient()
        client.util_get_guard_item = Mock(return_value=mock_guard_item)

        result = client.update_guard("some-id", mock_guard)

        client.util_get_guard_item.assert_called_once_with("some-id", mock_session)
        self.assertEqual(mock_guard_item.guard, {"name": "updated"})
        self.assertEqual(mock_guard_item.updated_at, "2024-01-01T00:00:00")
        mock_session.commit.assert_called_once()
        mock_from_guard_item.assert_called_once_with(mock_guard_item)
        self.assertEqual(result, mock_result)

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_raises_404_when_guard_not_found(self, mock_pg_client):
        """Test update_guard raises HttpError 404 when guard does not exist."""
        mock_session = Mock()
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        client = PGGuardClient()
        client.util_get_guard_item = Mock(return_value=None)

        with self.assertRaises(HttpError) as ctx:
            client.update_guard("missing-id", Mock())

        error = ctx.exception
        self.assertEqual(error.status, 404)
        self.assertEqual(error.message, "NotFound")
        self.assertIsNotNone(error.cause)
        self.assertIn("missing-id", error.cause)  # type: ignore[arg-type]


class TestUpsertGuard(unittest.TestCase):
    """Test cases for PGGuardClient.upsert_guard."""

    @patch("guardrails_api.clients.pg_guard_client.from_guard_item")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_updates_when_guard_exists(self, mock_pg_client, mock_from_guard_item):
        """Test upsert_guard updates existing guard."""
        mock_guard_item = Mock()
        mock_session = Mock()
        mock_session.execute.return_value.scalar.return_value = "2024-01-01T00:00:00"
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        mock_guard = Mock()
        mock_guard.model_dump.return_value = {"name": "updated"}
        mock_result = Mock()
        mock_from_guard_item.return_value = mock_result

        client = PGGuardClient()
        client.util_get_guard_item = Mock(return_value=mock_guard_item)

        result = client.upsert_guard("some-id", mock_guard)

        self.assertEqual(mock_guard_item.guard, {"name": "updated"})
        mock_session.commit.assert_called_once()
        mock_from_guard_item.assert_called_once_with(mock_guard_item)
        self.assertEqual(result, mock_result)

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_creates_when_guard_not_found(self, mock_pg_client):
        """Test upsert_guard creates a new guard when one does not exist."""
        mock_session = Mock()
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        mock_guard = Mock()
        mock_result = Mock()

        client = PGGuardClient()
        client.util_get_guard_item = Mock(return_value=None)
        client.util_create_guard = Mock(return_value=mock_result)

        result = client.upsert_guard("new-id", mock_guard)

        client.util_create_guard.assert_called_once_with(mock_guard, mock_session)
        self.assertEqual(result, mock_result)


class TestDeleteGuard(unittest.TestCase):
    """Test cases for PGGuardClient.delete_guard."""

    @patch("guardrails_api.clients.pg_guard_client.from_guard_item")
    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_deletes_existing_guard(self, mock_pg_client, mock_from_guard_item):
        """Test delete_guard deletes the item from db and returns it."""
        mock_guard_item = Mock()
        mock_session = Mock()
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        mock_result = Mock()
        mock_from_guard_item.return_value = mock_result

        client = PGGuardClient()
        client.util_get_guard_item = Mock(return_value=mock_guard_item)

        result = client.delete_guard("some-id")

        client.util_get_guard_item.assert_called_once_with("some-id", mock_session)
        mock_session.delete.assert_called_once_with(mock_guard_item)
        mock_session.commit.assert_called_once()
        mock_from_guard_item.assert_called_once_with(mock_guard_item)
        self.assertEqual(result, mock_result)

    @patch("guardrails_api.clients.pg_guard_client.PostgresClient")
    def test_raises_404_when_guard_not_found(self, mock_pg_client):
        """Test delete_guard raises HttpError 404 when guard does not exist."""
        mock_session = Mock()
        mock_pg_client.return_value.SessionLocal.return_value = mock_session

        client = PGGuardClient()
        client.util_get_guard_item = Mock(return_value=None)

        with self.assertRaises(HttpError) as ctx:
            client.delete_guard("missing-id")

        error = ctx.exception
        self.assertEqual(error.status, 404)
        self.assertEqual(error.message, "NotFound")
        self.assertIsNotNone(error.cause)
        self.assertIn("missing-id", error.cause)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
