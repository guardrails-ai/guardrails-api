#!/bin/bash


docker buildx build \
    --platform linux/arm64 \
    -f "./integration_tests/Dockerfile" \
    -t "guardrails-api:integration-tests" \
    --build-arg GUARDRAILS_TOKEN="$GUARDRAILS_TOKEN" \
    --progress plain \
    --load . \
    || exit 1