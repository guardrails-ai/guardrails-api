# Guardrails API Unit Tests

This directory contains comprehensive unit tests for the `guardrails_api` package using Python's built-in `unittest` framework.

## Test Structure

The tests are organized in subdirectories that mirror the source code structure, with test files named `test_{src_file_name}.py`:

```
tests/
├── __init__.py
├── README.md
├── classes/
│   ├── __init__.py
│   ├── test_health_check.py       (tests guardrails_api/classes/health_check.py)
│   └── test_http_error.py         (tests guardrails_api/classes/http_error.py)
├── clients/
│   ├── __init__.py
│   └── test_guard_client.py       (tests guardrails_api/clients/guard_client.py)
├── models/
│   ├── __init__.py
│   └── test_guard_item.py         (tests guardrails_api/models/guard_item.py)
├── otel/
│   ├── __init__.py
│   └── test_constants.py          (tests guardrails_api/otel/constants.py)
└── utils/
    ├── __init__.py
    ├── test_configuration.py
    ├── test_escape_curlys.py
    ├── test_file.py
    ├── test_gather_request_metrics.py
    ├── test_get_llm_callable.py
    ├── test_handle_error.py
    ├── test_has_internet_connection.py
    ├── test_logger.py
    ├── test_openai.py
    ├── test_payload_validator.py
    ├── test_pluck.py
    ├── test_remove_nones.py
    └── test_try_json_loads.py
```

### Classes Tests (`tests/classes/`)
- `test_health_check.py` - Tests for the HealthCheck class
- `test_http_error.py` - Tests for the HttpError exception class

### Client Tests (`tests/clients/`)
- `test_guard_client.py` - Tests for the base GuardClient interface

### Model Tests (`tests/models/`)
- `test_guard_item.py` - Tests for the GuardItem database model

### Utility Tests (`tests/utils/`)
- `test_pluck.py` - Tests for the pluck function
- `test_remove_nones.py` - Tests for the remove_nones function
- `test_try_json_loads.py` - Tests for the try_json_loads function
- `test_escape_curlys.py` - Tests for escape_curlys and descape_curlys functions
- `test_file.py` - Tests for file utilities
- `test_configuration.py` - Tests for configuration validation
- `test_has_internet_connection.py` - Tests for internet connectivity check
- `test_logger.py` - Tests for logger initialization
- `test_get_llm_callable.py` - Tests for LLM callable retrieval
- `test_gather_request_metrics.py` - Tests for request metrics decorator
- `test_handle_error.py` - Tests for error handling decorator
- `test_payload_validator.py` - Tests for payload validation
- `test_openai.py` - Tests for OpenAI response formatting

### OTEL Tests (`tests/otel/`)
- `test_constants.py` - Tests for OpenTelemetry constants

## Running the Tests

### Run all tests
```bash
source .venv/bin/activate
python -m unittest discover -s tests -p "test_*.py"
```

### Run all tests with verbose output
```bash
source .venv/bin/activate
python -m unittest discover -s tests -p "test_*.py" -v
```

### Run tests from a specific subdirectory
```bash
# Run all utils tests
source .venv/bin/activate
python -m unittest discover -s tests/utils -p "test_*.py"

# Run all classes tests
source .venv/bin/activate
python -m unittest discover -s tests/classes -p "test_*.py"
```

### Run a specific test file
```bash
source .venv/bin/activate
python -m unittest tests.utils.test_pluck
```

### Run a specific test class
```bash
source .venv/bin/activate
python -m unittest tests.utils.test_pluck.TestPluck
```

### Run a specific test method
```bash
source .venv/bin/activate
python -m unittest tests.utils.test_pluck.TestPluck.test_pluck_with_existing_keys
```

### Use the test runner script
```bash
./run_tests.sh
```

## Test Coverage

The test suite includes:
- **146 test cases** covering the core functionality
- Unit tests for utility functions
- Tests for data models and classes
- Tests for client interfaces
- Tests for decorators and error handling
- Mock-based tests for external dependencies

### Test Distribution
- **Classes**: 19 tests
- **Clients**: 8 tests
- **Models**: 9 tests
- **Utils**: 107 tests
- **OTEL**: 3 tests

## Test Principles

- All tests use Python's built-in `unittest` framework (no pytest)
- Tests are isolated and independent
- External dependencies are mocked using `unittest.mock`
- Async functions are tested using `asyncio.run()`
- Temporary files are properly cleaned up in tearDown methods
- Each test has a clear docstring explaining what it tests
- Directory structure mirrors the source code structure
- Test files are named `test_{src_file_name}.py` to match their source counterparts

## Adding New Tests

When adding new tests:
1. Determine which subdirectory the test belongs to based on the source module location
2. Create a new file named `test_{src_file_name}.py` in the appropriate subdirectory
   - For `guardrails_api/utils/my_function.py` → create `tests/utils/test_my_function.py`
   - For `guardrails_api/classes/my_class.py` → create `tests/classes/test_my_class.py`
3. Import unittest and the module to test
4. Create test classes inheriting from `unittest.TestCase`
5. Name test methods starting with `test_`
6. Add descriptive docstrings to each test
7. Use setUp/tearDown for initialization and cleanup
8. Mock external dependencies appropriately

Example for testing `guardrails_api/utils/my_function.py`:
```python
"""Unit tests for guardrails_api.utils.my_function module."""
import unittest
from guardrails_api.utils.my_function import my_function

class TestMyFunction(unittest.TestCase):
    """Test cases for my_function."""

    def test_basic_functionality(self):
        """Test basic functionality of my_function."""
        result = my_function("input")
        self.assertEqual(result, "expected")

if __name__ == "__main__":
    unittest.main()
```

Save this file as `tests/utils/test_my_function.py`.

## Naming Convention

Test files follow the pattern `test_{src_file_name}.py`:
- Source: `guardrails_api/utils/pluck.py` → Test: `tests/utils/test_pluck.py`
- Source: `guardrails_api/classes/health_check.py` → Test: `tests/classes/test_health_check.py`
- Source: `guardrails_api/otel/constants.py` → Test: `tests/otel/test_constants.py`

This naming convention makes it easy to find the corresponding test file for any source file.
