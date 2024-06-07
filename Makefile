# Installs production dependencies
install:
	pip install .;

# Installs development dependencies
install-dev:
	pip install .[dev];

lock:
	pip freeze --exclude guardrails-api-client > requirements-lock.txt

install-lock:
	pip install -r requirements-lock.txt

.PHONY: build
build:
	curl https://raw.githubusercontent.com/guardrails-ai/guardrails-api-client/main/service-specs/guardrails-service-spec.yml -o ./open-api-spec.yml
	npx @redocly/cli bundle --dereferenced --output ./guardrails_api/open-api-spec.json --ext json ./open-api-spec.yml

start:
	bash ./guardrails_api/start.sh

infra:
	docker compose --profile infra up --build

env:
	if [ ! -d "./.venv" ]; then echo "Creating virtual environment..."; python3 -m venv ./.venv; fi;

refresh:
	echo "Removing old virtual environment"
	rm -rf ./.venv;
	echo "Creating new virtual environment"
	python3 -m venv ./.venv;
	echo "Sourcing and installing"
	source ./.venv/bin/activate && make install-lock;


format:
	ruff check guardrails_api/ tests/ --fix
	ruff format guardrails_api/ tests/


lint:
	ruff check guardrails_api/ tests/
	ruff format guardrails_api/ tests/

qa:
	make build
	make lint
	make test-cov

# This doesn't actually work, but it's nice to be able to just copy/paste instead of typing this out in the terminal.
source:
	source ./.venv/bin/activate

test:
	pytest ./tests

test-cov:
	coverage run --source=./guardrails_api -m pytest ./tests
	coverage report --fail-under=45

view-test-cov:
	coverage run --source=./guardrails_api -m pytest ./tests
	coverage html
	open htmlcov/index.html