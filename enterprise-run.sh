docker stop guardrails-api-enterprise || true
docker rm guardrails-api-enterprise || true
docker run -p 8000:8000 --env-file local.env --name guardrails-api-enterprise -it guardrails-api-enterprise:latest