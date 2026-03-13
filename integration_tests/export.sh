docker container stop guardrails-server || true
docker container rm guardrails-server || true
docker container create --name guardrails-server guardrails-api:integration-tests
docker container export guardrails-server > ./guardrails-server.tar