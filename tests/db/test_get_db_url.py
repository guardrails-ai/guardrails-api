"""Unit tests for guardrails_api.db.get_db_url module."""

import unittest
from unittest.mock import patch
from guardrails_api.db.get_db_url import get_db_url


class TestGetDbUrl(unittest.TestCase):
    @patch.dict(
        "os.environ", {"DB_URL": "postgresql://user:pass@host:5432/db"}, clear=True
    )
    def test_returns_db_url_when_set(self):
        """DB_URL takes precedence over individual PG* vars."""
        result = get_db_url()
        self.assertEqual(result, "postgresql://user:pass@host:5432/db")

    @patch.dict(
        "os.environ",
        {
            "DB_URL": "postgresql://user:pass@host:5432/db",
            "PGHOST": "other-host",
            "PGUSER": "other-user",
        },
        clear=True,
    )
    def test_db_url_takes_precedence_over_pg_vars(self):
        """DB_URL is returned even when PG* vars are also set."""
        result = get_db_url()
        self.assertEqual(result, "postgresql://user:pass@host:5432/db")

    @patch.dict(
        "os.environ",
        {
            "PGUSER": "myuser",
            "PGPASSWORD": "mypassword",
            "PGHOST": "localhost",
            "PGPORT": "5432",
            "PGDATABASE": "mydb",
        },
        clear=True,
    )
    def test_builds_url_from_pg_vars(self):
        """Constructs a valid postgresql:// URL from individual PG* vars."""
        result = get_db_url()
        self.assertEqual(result, "postgresql://myuser:mypassword@localhost:5432/mydb")

    @patch.dict(
        "os.environ",
        {
            "PGUSER": "myuser",
            "PGPASSWORD": "mypassword",
            "PGHOST": "localhost",
            "PGPORT": "5432",
            "PGDATABASE": "mydb",
            "DB_EXTRAS": "?sslmode=require",
        },
        clear=True,
    )
    def test_appends_db_extras(self):
        """DB_EXTRAS is appended to the constructed URL."""
        result = get_db_url()
        self.assertEqual(
            result,
            "postgresql://myuser:mypassword@localhost:5432/mydb?sslmode=require",
        )

    @patch.dict("os.environ", {}, clear=True)
    def test_all_vars_missing_returns_empty_template(self):
        """Returns the URL template with empty strings when no env vars are set."""
        result = get_db_url()
        self.assertEqual(result, "postgresql://:@:/")

    @patch.dict("os.environ", {"PGHOST": "localhost"}, clear=True)
    def test_partial_vars_leaves_missing_fields_empty(self):
        """Missing individual PG* vars default to empty string."""
        result = get_db_url()
        self.assertEqual(result, "postgresql://:@localhost:/")

    @patch.dict(
        "os.environ",
        {
            "PGUSER": "admin",
            "PGPASSWORD": "s3cr3t",
            "PGHOST": "db.example.com",
            "PGPORT": "5433",
            "PGDATABASE": "prod",
            "DB_EXTRAS": "?connect_timeout=10&application_name=api",
        },
        clear=True,
    )
    def test_multiple_db_extras_params(self):
        """Multiple query parameters in DB_EXTRAS are included verbatim."""
        result = get_db_url()
        self.assertEqual(
            result,
            "postgresql://admin:s3cr3t@db.example.com:5433/prod?connect_timeout=10&application_name=api",
        )

    @patch.dict("os.environ", {"DB_URL": ""}, clear=True)
    def test_empty_db_url_falls_through_to_pg_vars(self):
        """An empty DB_URL is falsy, so PG* vars are used instead."""
        result = get_db_url()
        self.assertEqual(result, "postgresql://:@:/")

    @patch.dict(
        "os.environ",
        {
            "PGUSER": "u",
            "PGPASSWORD": "p",
            "PGHOST": "h",
            "PGPORT": "5432",
            "PGDATABASE": "d",
        },
        clear=True,
    )
    def test_returns_string(self):
        """Return value is always a string."""
        result = get_db_url()
        self.assertIsInstance(result, str)

    @patch.dict(
        "os.environ", {"DB_URL": "postgresql://user:pass@host:5432/db"}, clear=True
    )
    def test_db_url_return_value_is_string(self):
        """Return value is a string when DB_URL is set."""
        result = get_db_url()
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
