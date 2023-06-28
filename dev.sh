#!/bin/bash
pip uninstall -y guardrails-ai
rm -rf ./guardrails-sdk
cp -r ../guardrails ./guardrails-sdk
pip install ../guardrails
docker-compose -f docker-compose-dev.yml up --build