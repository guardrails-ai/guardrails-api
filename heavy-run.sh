docker stop guardrails-api-heavy || true
docker rm guardrails-api-heavy || true
docker run -p 8000:8000 --env-file local.env --name guardrails-api-heavy -it graas-heavy:latest