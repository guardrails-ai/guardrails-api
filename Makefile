.PHONY: install install-dev lock install-lock build serve db env refresh format lint qa test test-cov view-test-cov
# Installs production dependencies
install:
	pip install .;

# Installs development dependencies
install-dev:
	pip install -e ".[dev]";
	pre-commit install

lock:
	pip freeze --exclude guardrails-api > requirements-lock.txt

install-lock:
	pip install -r requirements-lock.txt

build:
	make install
	
	cp "$$(python -c "import guardrails_api_client as _; print(_.__path__[0])")/openapi-spec.json" ./guardrails_api/open-api-spec.json
	

serve:
	python ./guardrails_api/app.py

db:
	docker compose up

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

test:
	python -m unittest discover -s tests --buffer --failfast

test-cov:
	coverage run -m unittest discover --start-directory tests --buffer --failfast
	coverage report -m

test-cov-ci:
	coverage run -m unittest discover --start-directory tests --buffer --failfast

view-test-cov:
	coverage run -m unittest discover --start-directory tests --buffer --failfast
	coverage html
	open htmlcov/index.html