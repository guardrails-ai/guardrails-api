# Installs production dependencies
install:
	pip install -r requirements.txt;
	opentelemetry-bootstrap -a install

# Installs development dependencies
install-dev:
	make install
	pip install -r requirements-dev.txt;

lock:
	pip freeze --exclude guardrails-api-client > requirements-lock.txt

install-lock:
	pip install -r requirements-lock.txt

build:
	make install

dev:
	bash ./dev.sh

local:
	python3 ./wsgi.py

env:
	if [ ! -d "./.venv" ]; then echo "Creating virtual environment..."; python3 -m venv ./.venv; fi;

format:
	black -l 80 ./src app.py wsgi.py

lint:
	flake8 --count ./src app.py wsgi.py

qa:
	make lint
	make test-cov

# This doesn't actually work, but it's nice to be able to just copy/paste instead of typing this out in the terminal.
source:
	source ./.venv/bin/activate

test:
	python3 -m pytest ./tests

test-cov:
	coverage run --source=./src -m pytest ./tests
	coverage report --fail-under=70

view-test-cov:
	coverage run --source=./src -m pytest ./tests
	coverage html
	open htmlcov/index.html