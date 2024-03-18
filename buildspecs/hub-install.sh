#!/bin/bash

echo " !!!!!!!!!!!! START HUB INSTALL !!!!!!!!!!!!"

index_json=$(curl -H "Authorization: token $GITHUB_TOKEN" https://raw.githubusercontent.com/guardrails-ai/guardrails-hub/main/index.json)

jq -r '.[].id' <<< $index_json | while read -r validator_id; do
    if $validator_id != "guardrails/wiki_provenance"; then
        guardrails hub install "hub://${validator_id}"
    fi
done

echo " !!!!!!!!!!!! END HUB INSTALL !!!!!!!!!!!!"