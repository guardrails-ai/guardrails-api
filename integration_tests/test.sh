#!/bin/bash

python -m venv integration_tests/.venv && \
source integration_tests/.venv/bin/activate && \
pip install . && \
pip install -r integration_tests/requirements.txt && \
integration_tests/.venv/bin/pytest integration_tests/tests || exit 1