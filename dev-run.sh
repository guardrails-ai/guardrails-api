docker stop guardrails-api-dev || true
docker rm guardrails-api-dev || true
docker run -p 8000:8000 --name guardrails-api-dev -it guardrails-api:dev