#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Run tests with color output and verbose mode
echo "Running Guardrails API Unit Tests..."
echo "====================================="
echo ""

python -m unittest discover -s tests -p "test_*.py" -v

# Capture exit code
EXIT_CODE=$?

echo ""
echo "====================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed. Exit code: $EXIT_CODE"
fi

exit $EXIT_CODE
