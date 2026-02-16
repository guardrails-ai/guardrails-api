"""Unit tests for guardrails_api.models.guard_item_audit module."""

import unittest
from datetime import datetime
from guardrails_api.models.guard_item_audit import GuardItemAudit


class TestGuardItemAudit(unittest.TestCase):
    """Test cases for the GuardItemAudit model."""

    def test_guard_item_audit_initialization(self):
        """Test GuardItemAudit initialization with all parameters."""
        railspec = {"validators": ["test_validator"]}
        timestamp = datetime.now()

        audit = GuardItemAudit(
            id="audit-123",
            name="test_guard",
            railspec=railspec,
            num_reasks=3,
            description="Test guard audit",
            replaced_on=timestamp,
            operation="U",
        )

        self.assertEqual(audit.id, "audit-123")
        self.assertEqual(audit.name, "test_guard")
        self.assertEqual(audit.railspec, railspec)
        self.assertEqual(audit.num_reasks, 3)
        self.assertEqual(audit.description, "Test guard audit")
        self.assertEqual(audit.replaced_on, timestamp)
        self.assertEqual(audit.operation, "U")

    def test_guard_item_audit_with_none_values(self):
        """Test GuardItemAudit with None optional fields."""
        timestamp = datetime.now()

        audit = GuardItemAudit(
            id="audit-456",
            name="minimal_guard",
            railspec={},
            num_reasks=None,
            description=None,
            replaced_on=timestamp,
            operation="D",
        )

        self.assertEqual(audit.id, "audit-456")
        self.assertEqual(audit.name, "minimal_guard")
        self.assertIsNone(audit.num_reasks)
        self.assertIsNone(audit.description)
        self.assertEqual(audit.operation, "D")

    def test_guard_item_audit_tablename(self):
        """Test that GuardItemAudit has correct table name."""
        self.assertEqual(GuardItemAudit.__tablename__, "guards_audit")

    def test_guard_item_audit_operation_insert(self):
        """Test GuardItemAudit with insert operation."""
        timestamp = datetime.now()

        audit = GuardItemAudit(
            id="audit-789",
            name="new_guard",
            railspec={"validators": []},
            num_reasks=0,
            description="New guard created",
            replaced_on=timestamp,
            operation="I",
        )

        self.assertEqual(audit.operation, "I")

    def test_guard_item_audit_operation_update(self):
        """Test GuardItemAudit with update operation."""
        timestamp = datetime.now()

        audit = GuardItemAudit(
            id="audit-abc",
            name="updated_guard",
            railspec={"validators": []},
            num_reasks=1,
            description="Guard updated",
            replaced_on=timestamp,
            operation="U",
        )

        self.assertEqual(audit.operation, "U")

    def test_guard_item_audit_operation_delete(self):
        """Test GuardItemAudit with delete operation."""
        timestamp = datetime.now()

        audit = GuardItemAudit(
            id="audit-def",
            name="deleted_guard",
            railspec={"validators": []},
            num_reasks=2,
            description="Guard deleted",
            replaced_on=timestamp,
            operation="D",
        )

        self.assertEqual(audit.operation, "D")

    def test_guard_item_audit_with_complex_railspec(self):
        """Test GuardItemAudit with complex railspec."""
        railspec = {
            "validators": [
                {"name": "validator1", "params": {"key": "value"}},
                {"name": "validator2", "params": {"key2": "value2"}},
            ],
            "output_schema": {"type": "object", "properties": {}},
        }
        timestamp = datetime.now()

        audit = GuardItemAudit(
            id="audit-complex",
            name="complex_guard",
            railspec=railspec,
            num_reasks=5,
            description="Complex guard",
            replaced_on=timestamp,
            operation="U",
        )

        self.assertEqual(audit.railspec, railspec)
        self.assertEqual(len(audit.railspec["validators"]), 2)

    def test_guard_item_audit_id_is_primary_key(self):
        """Test that id field is used as primary key."""
        timestamp = datetime.now()

        audit = GuardItemAudit(
            id="primary-key-test",
            name="test",
            railspec={},
            num_reasks=0,
            description="",
            replaced_on=timestamp,
            operation="I",
        )

        self.assertEqual(audit.id, "primary-key-test")


if __name__ == "__main__":
    unittest.main()
