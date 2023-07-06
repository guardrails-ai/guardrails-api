#!/bin/bash
version=$(cat .version)
rm -rf ./sdk
npx autorest \
  --input-file=./open-api-spec.yml \
  --output-folder=./sdk \
  --namespace=guardrails-api-client \
  --package-version=$version \
  --python \
  --basic-setup-py