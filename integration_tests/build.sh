#!/bin/bash


docker buildx build \
    --platform linux/arm64 \
    -f "./integration_tests/Dockerfile.w_config" \
    -t "guardrails-api:integration-tests" \
    --secret id=GUARDRAILS_TOKEN \
    --progress plain \
    --load . \
    || exit 1