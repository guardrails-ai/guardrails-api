build-sdk:
	bash build-sdk.sh

dev:
	bash ./dev.sh

env:
	if [ ! -d "./.venv" ]; then echo "Creating virtual environment..."; python3 -m venv ./.venv; fi;

format:
	black -l 80 ./src app.py wsgi.py

install:
	pip install -r requirements.txt

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
	coverage report --fail-under=0 ## TODO: Update with real coverage threshold after tests are backfilled

view-test-cov:
	coverage run --source=./src -m pytest ./tests
	coverage html
	open htmlcov/index.html