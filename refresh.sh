#!/bin/bash

echo "Deactivating old virtual environment"
deactivate

echo "Deleting old virtual environment"
rm -rf ./.venv

echo "Creating new virtual environment"
python3 -m venv ./.venv

echo "Sourcing new virtual environment"
source ./.venv/bin/activate

echo "Installing dependencies"
pip install -r requirements.txt --no-cache-dir;
# make install
# make install-dev