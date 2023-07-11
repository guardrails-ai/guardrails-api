#!/bin/bash
pip install openapi-python-client;
version=$(yq '.info.version' open-api-spec.yml);
rm -rf ./guard-rails-api-client;
openapi-python-client generate --path ./open-api-spec.yml --meta setup;