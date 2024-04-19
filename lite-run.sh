docker stop guardrails-api-lite || true
docker rm guardrails-api-lite || true
docker run -p 8000:8000 --env-file local.env --name guardrails-api-lite -it guardrails-api:lite
