#!/bin/bash

echo "Deactivating old virtual environment"
deactivate

echo "Deleting old virtual environment"
rm -rf ./.venv

echo "Creating new virtual environment"
python3 -m venv ./.venv

echo "Sourcing new virtual environment"
source ./.venv/bin/activate

echo "Installing guardrails"
make install-dev

echo "building..."
make build