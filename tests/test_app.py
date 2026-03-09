"""Unit tests for guardrails_api.app module."""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from guardrails_api.app import (
    CustomJSONEncoder,
    create_app,
    register_config,
    register_middleware,
)


class TestCustomJSONEncoder(unittest.TestCase):
    """Tests for CustomJSONEncoder.default()"""

    def setUp(self):
        self.encoder = CustomJSONEncoder()

    def test_encodes_set_as_list(self):
        result = self.encoder.default({1, 2, 3})
        self.assertIsInstance(result, list)
        self.assertEqual(sorted(result), [1, 2, 3])

    def test_encodes_empty_set(self):
        result = self.encoder.default(set())
        self.assertEqual(result, [])

    def test_encodes_callable_as_string(self):
        def my_func():
            pass

        result = self.encoder.default(my_func)
        self.assertIsInstance(result, str)

    def test_encodes_lambda_as_string(self):
        fn = lambda x: x  # noqa: E731
        result = self.encoder.default(fn)
        self.assertIsInstance(result, str)

    def test_raises_for_unhandled_type(self):
        with self.assertRaises(TypeError):
            self.encoder.default(object())

    def test_full_serialization_with_set(self):
        data = {"values": {1, 2, 3}}
        result = json.loads(json.dumps(data, cls=CustomJSONEncoder))
        self.assertIsInstance(result["values"], list)
        self.assertEqual(sorted(result["values"]), [1, 2, 3])

    def test_full_serialization_with_callable(self):
        def my_func():
            pass

        data = {"fn": my_func}
        result = json.loads(json.dumps(data, cls=CustomJSONEncoder))
        self.assertIsInstance(result["fn"], str)


class TestRegisterConfig(unittest.TestCase):
    """Tests for register_config()"""

    @patch("guardrails_api.app.importlib.util.spec_from_file_location")
    @patch("guardrails_api.app.os.path.isfile", return_value=True)
    def test_loads_config_when_file_exists(self, _, mock_spec_from_loc):
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_loc.return_value = mock_spec

        mock_module = MagicMock()
        with patch(
            "guardrails_api.app.importlib.util.module_from_spec",
            return_value=mock_module,
        ):
            register_config("/some/path/config.py")

        mock_spec.loader.exec_module.assert_called_once_with(mock_module)

    @patch("guardrails_api.app.os.path.isfile", return_value=False)
    def test_skips_load_when_file_missing(self, _):
        with patch(
            "guardrails_api.app.importlib.util.spec_from_file_location"
        ) as mock_spec:
            register_config("/nonexistent/config.py")
            mock_spec.assert_not_called()

    def test_returns_absolute_path_for_custom_config(self):
        with patch("guardrails_api.app.os.path.isfile", return_value=False):
            result = register_config("/some/path/config.py")
            self.assertTrue(os.path.isabs(result))

    def test_uses_default_config_when_none_provided(self):
        with patch("guardrails_api.app.os.path.isfile", return_value=False):
            result = register_config(None)
            expected = os.path.abspath(os.path.join(os.getcwd(), "./config.py"))
            self.assertEqual(result, expected)

    @patch(
        "guardrails_api.app.importlib.util.spec_from_file_location", return_value=None
    )
    @patch("guardrails_api.app.os.path.isfile", return_value=True)
    def test_handles_none_spec(self, *_):
        result = register_config("/some/path/config.py")
        self.assertIsNotNone(result)

    @patch("guardrails_api.app.os.path.isfile", return_value=True)
    def test_handles_spec_with_no_loader(self, _):
        mock_spec = MagicMock()
        mock_spec.loader = None
        with patch(
            "guardrails_api.app.importlib.util.spec_from_file_location",
            return_value=mock_spec,
        ):
            result = register_config("/some/path/config.py")
            self.assertIsNotNone(result)

    def test_returns_path_as_string(self):
        with patch("guardrails_api.app.os.path.isfile", return_value=False):
            result = register_config("/tmp/config.py")
            self.assertIsInstance(result, str)

    def test_custom_path_overrides_default(self):
        custom_path = "/custom/myconfig.py"
        with patch("guardrails_api.app.os.path.isfile", return_value=False):
            result = register_config(custom_path)
            self.assertEqual(result, os.path.abspath(custom_path))


class TestRegisterMiddleware(unittest.TestCase):
    """Tests for register_middleware()"""

    def _make_app(self):
        return MagicMock(spec=FastAPI)

    @patch("guardrails_api.app.os.path.isfile", return_value=False)
    def test_skips_when_no_middleware_file(self, _):
        app = self._make_app()
        register_middleware(middleware="/nonexistent/middleware.py", app=app)
        app.add_middleware.assert_not_called()

    @patch("guardrails_api.app.os.path.isfile", return_value=True)
    def test_uses_default_middleware_path_when_none_provided(self, _):
        app = self._make_app()
        with patch(
            "guardrails_api.app.importlib.util.spec_from_file_location"
        ) as mock_spec_fn:
            mock_spec = MagicMock()
            mock_spec.loader = None  # skip loading
            mock_spec_fn.return_value = mock_spec
            register_middleware(middleware=None, app=app)
            expected_path = os.path.abspath(
                os.path.join(os.getcwd(), "./middleware.py")
            )
            mock_spec_fn.assert_called_once_with("middleware", expected_path)

    @patch("guardrails_api.app.os.path.isfile", return_value=True)
    def test_adds_valid_middleware_class(self, _):
        app = self._make_app()

        class MyMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                return await call_next(request)

        mock_module = MagicMock()
        mock_module.__dir__ = MagicMock(return_value=["MyMiddleware"])
        mock_module.MyMiddleware = MyMiddleware

        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()

        with (
            patch(
                "guardrails_api.app.importlib.util.spec_from_file_location",
                return_value=mock_spec,
            ),
            patch(
                "guardrails_api.app.importlib.util.module_from_spec",
                return_value=mock_module,
            ),
        ):
            register_middleware(middleware="/path/middleware.py", app=app)

        app.add_middleware.assert_called_once_with(MyMiddleware)

    @patch("guardrails_api.app.os.path.isfile", return_value=True)
    def test_skips_non_middleware_exports(self, _):
        app = self._make_app()

        class NotMiddleware:
            pass

        mock_module = MagicMock()
        mock_module.__dir__ = MagicMock(return_value=["NotMiddleware", "some_function"])
        mock_module.NotMiddleware = NotMiddleware
        mock_module.some_function = lambda: None

        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()

        with (
            patch(
                "guardrails_api.app.importlib.util.spec_from_file_location",
                return_value=mock_spec,
            ),
            patch(
                "guardrails_api.app.importlib.util.module_from_spec",
                return_value=mock_module,
            ),
        ):
            register_middleware(middleware="/path/middleware.py", app=app)

        app.add_middleware.assert_not_called()

    @patch("guardrails_api.app.os.path.isfile", return_value=True)
    def test_skips_base_http_middleware_itself(self, _):
        """BaseHTTPMiddleware should not be registered as middleware."""
        app = self._make_app()

        mock_module = MagicMock()
        mock_module.__dir__ = MagicMock(return_value=["BaseHTTPMiddleware"])
        mock_module.BaseHTTPMiddleware = BaseHTTPMiddleware

        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()

        with (
            patch(
                "guardrails_api.app.importlib.util.spec_from_file_location",
                return_value=mock_spec,
            ),
            patch(
                "guardrails_api.app.importlib.util.module_from_spec",
                return_value=mock_module,
            ),
        ):
            register_middleware(middleware="/path/middleware.py", app=app)

        app.add_middleware.assert_not_called()

    @patch("guardrails_api.app.os.path.isfile", return_value=True)
    def test_adds_multiple_middleware_classes(self, _):
        app = self._make_app()

        class MiddlewareA(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                return await call_next(request)

        class MiddlewareB(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                return await call_next(request)

        mock_module = MagicMock()
        mock_module.__dir__ = MagicMock(return_value=["MiddlewareA", "MiddlewareB"])
        mock_module.MiddlewareA = MiddlewareA
        mock_module.MiddlewareB = MiddlewareB

        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()

        with (
            patch(
                "guardrails_api.app.importlib.util.spec_from_file_location",
                return_value=mock_spec,
            ),
            patch(
                "guardrails_api.app.importlib.util.module_from_spec",
                return_value=mock_module,
            ),
        ):
            register_middleware(middleware="/path/middleware.py", app=app)

        self.assertEqual(app.add_middleware.call_count, 2)
        app.add_middleware.assert_any_call(MiddlewareA)
        app.add_middleware.assert_any_call(MiddlewareB)

    @patch("guardrails_api.app.os.path.isfile", return_value=True)
    def test_handles_none_spec(self, _):
        app = self._make_app()
        with patch(
            "guardrails_api.app.importlib.util.spec_from_file_location",
            return_value=None,
        ):
            register_middleware(middleware="/path/middleware.py", app=app)
        app.add_middleware.assert_not_called()


class TestCreateApp(unittest.TestCase):
    """Tests for create_app()"""

    def setUp(self):
        self.mock_guard_client = MagicMock()
        self.mock_guard_client.get_guards.return_value = []
        self.mock_cache_instance = MagicMock()
        mock_cache_cls = MagicMock(return_value=self.mock_cache_instance)

        self._patches = [
            patch("guardrails_api.app.Console"),
            patch(
                "guardrails_api.app.register_config", return_value="/resolved/config.py"
            ),
            patch("guardrails_api.app.register_middleware"),
            patch("guardrails_api.app.configure_logging"),
            patch("guardrails_api.app.postgres_is_enabled", return_value=False),
            patch("guardrails_api.app.CacheClient", mock_cache_cls),
            patch("builtins.__import__", side_effect=self._make_import_side_effect()),
        ]
        self.mocks = {p.attribute: p.start() for p in self._patches}

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def _make_import_side_effect(self, pg_client_cls=None):
        real_import = __import__
        guard_client = self.mock_guard_client

        def side_effect(name, *args, **kwargs):
            if name == "guardrails_api.db.postgres_client" and pg_client_cls:
                mod = MagicMock()
                mod.PostgresClient = pg_client_cls
                return mod
            if name == "guardrails_api.clients.get_guard_client":
                mod = MagicMock()
                mod.get_guard_client = MagicMock(return_value=guard_client)
                return mod
            return real_import(name, *args, **kwargs)

        return side_effect

    def test_returns_fastapi_app(self):
        result = create_app()
        self.assertIsInstance(result, FastAPI)

    def test_sets_self_endpoint_env_var(self):
        with patch.dict(
            "os.environ", {"HOST": "http://myhost", "SELF_ENDPOINT": ""}, clear=False
        ):
            create_app(port=9000)
            self.assertEqual(os.environ.get("SELF_ENDPOINT"), "http://myhost:9000")

    def test_uses_provided_self_endpoint_env_var(self):
        with patch.dict(
            "os.environ", {"SELF_ENDPOINT": "http://custom:1234"}, clear=False
        ):
            create_app()
            self.assertEqual(os.environ.get("SELF_ENDPOINT"), "http://custom:1234")

    def test_calls_register_config(self):
        # Stop the generic register_config patch so we can assert on it
        register_config_patch = next(
            p for p in self._patches if p.attribute == "register_config"
        )
        register_config_patch.stop()
        self._patches.remove(register_config_patch)

        with patch(
            "guardrails_api.app.register_config", return_value="/resolved/config.py"
        ) as mock_cfg:
            create_app(config="/my/config.py")

        mock_cfg.assert_called_once_with("/my/config.py")

    def test_calls_configure_logging(self):
        configure_logging_patch = next(
            p for p in self._patches if p.attribute == "configure_logging"
        )
        configure_logging_patch.stop()
        self._patches.remove(configure_logging_patch)

        with (
            patch.dict("os.environ", {"GUARDRAILS_LOG_LEVEL": "DEBUG"}, clear=False),
            patch("guardrails_api.app.configure_logging") as mock_log,
        ):
            create_app()

        mock_log.assert_called_once_with(log_level="DEBUG")

    def test_cache_client_initialized(self):
        create_app()
        self.mock_cache_instance.initialize.assert_called_once()

    def test_postgres_client_initialized_when_enabled(self):
        mock_pg_client = MagicMock()
        mock_pg_client_cls = MagicMock(return_value=mock_pg_client)

        # Restart the __import__ patch with pg support, and override postgres_is_enabled
        import_patch = next(p for p in self._patches if p.attribute == "__import__")
        import_patch.stop()
        self._patches.remove(import_patch)

        pg_patch = next(
            p for p in self._patches if p.attribute == "postgres_is_enabled"
        )
        pg_patch.stop()
        self._patches.remove(pg_patch)

        with (
            patch("guardrails_api.app.postgres_is_enabled", return_value=True),
            patch(
                "builtins.__import__",
                side_effect=self._make_import_side_effect(mock_pg_client_cls),
            ),
        ):
            create_app()

        mock_pg_client.initialize.assert_called_once()

    def test_loads_dotenv_when_env_provided(self):
        mock_load_dotenv = MagicMock()
        mock_dotenv = MagicMock()
        mock_dotenv.load_dotenv = mock_load_dotenv
        real_import = __import__
        guard_client = self.mock_guard_client

        import_patch = next(p for p in self._patches if p.attribute == "__import__")
        import_patch.stop()
        self._patches.remove(import_patch)

        def import_side_effect(name, *args, **kwargs):
            if name == "dotenv":
                return mock_dotenv
            if name == "guardrails_api.clients.get_guard_client":
                mod = MagicMock()
                mod.get_guard_client = MagicMock(return_value=guard_client)
                return mod
            return real_import(name, *args, **kwargs)

        with (
            patch("builtins.__import__", side_effect=import_side_effect),
            patch("guardrails_api.app.os.path.isfile") as mock_isfile,
        ):
            mock_isfile.return_value = True
            create_app(env="/path/to/.env")

        mock_load_dotenv.assert_called_once()

    def test_no_dotenv_when_env_not_provided(self):
        mock_load_dotenv = MagicMock()
        create_app(env=None)
        mock_load_dotenv.assert_not_called()

    def test_exception_handler_registered(self):
        result = create_app()
        self.assertIn(ValueError, result.exception_handlers)


if __name__ == "__main__":
    unittest.main()
