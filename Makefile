# Installs production dependencies
install:
	pip install -r requirements.txt;
	# This is a workaround because of this issue: https://github.com/open-telemetry/opentelemetry-python-contrib/issues/2053
	pip uninstall aiohttp -y
	pip install opentelemetry-distro
	opentelemetry-bootstrap -a install
	pip install aiohttp

# Installs development dependencies
install-dev:
	make install
	pip install -r requirements-dev.txt;

lock:
	pip freeze --exclude guardrails-api-client > requirements-lock.txt

install-lock:
	pip install -r requirements-lock.txt

start:
	bash start.sh

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
	ruff check app.py wsgi.py src/ tests/ --fix
	ruff format app.py wsgi.py src/ tests/


lint:
	ruff check app.py wsgi.py src/ tests/
	ruff format app.py wsgi.py src/ tests/

qa:
	make lint
	make test-cov

# This doesn't actually work, but it's nice to be able to just copy/paste instead of typing this out in the terminal.
source:
	source ./.venv/bin/activate

test:
	pytest ./tests

test-cov:
	coverage run --source=./src -m pytest ./tests
	coverage report --fail-under=50

view-test-cov:
	coverage run --source=./src -m pytest ./tests
	coverage html
	open htmlcov/index.html