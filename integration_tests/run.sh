#!/bin/bash


docker stop guardrails-server || true
docker rm guardrails-server || true
docker run -d --name guardrails-server -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY guardrails-api:integration-tests || exit 1