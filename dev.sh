#!/bin/bash
pip uninstall -y guardrails-ai
rm -rf ./guardrails-sdk
cp -r ../guardrails ./guardrails-sdk
pip install ../guardrails

mkdir -p ./pgadmin-data

cp ./pgadmin-dev-server.json ./pgadmin-data/servers.json
PG_PASSWORD="${PGPASSWORD:-changeme}"
echo "$PG_PASSWORD" > ./pgadmin-data/passfile

docker-compose -f docker-compose-dev.yml up --build