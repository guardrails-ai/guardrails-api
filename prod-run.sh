docker stop guardrails-api-prod || true
docker rm guardrails-api-prod || true
docker run -p 8000:8000 --env-file local-prod.env --name guardrails-api-prod -it guardrails-api:prod