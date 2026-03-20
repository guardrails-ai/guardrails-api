.PHONY: install install-dev lock install-lock build bootstrap serve db env refresh format lint qa test test-cov view-test-cov type generate custom-gen
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

bootstrap:
	opentelemetry-bootstrap -a install
	

serve:
	guardrails-api start --env ./.env

serve-w-otel:
	source ./.env.sh && opentelemetry-instrument guardrails-api start

# Only launch the postgres database from docker compose
db:
	docker compose --profile db up

# Launch the postgres database, jaeger, and otel collector from docker compose
infra:
	docker compose --profile infra up

# Launch the postgres database and guardrails server from docker compose
docker-serve:
	docker compose --profile db --profile server up

# Launch all services from docker compose
docker-serve-all:
	docker compose --profile all up

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

type:
	pyright

qa:
	make lint
	make type
	make test-cov

test:
	python -m unittest discover -s tests --buffer --failfast

test-single:
	python -m unittest tests.cli.__init__.TestVersionCallback

test-cov:
	coverage run -m unittest discover --start-directory tests --buffer --failfast
	coverage report -m

test-cov-ci:
	coverage run -m unittest discover --start-directory tests --buffer --failfast

view-test-cov:
	coverage run --source=guardrails_api -m unittest discover --start-directory tests --buffer --failfast
	coverage html
	open htmlcov/index.html

generate:
	# Example Usage: make generate M="my message here"
	GR_DEV="true" alembic -c guardrails_api/db/migrations/alembic.ini revision --autogenerate -m "${M}"

custom-gen:
	# Example Usage: make generate M="my message here"
	GR_DEV="true" alembic -c guardrails_api/db/migrations/alembic.ini revision -m "${M}"