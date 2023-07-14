build-sdk:
	bash build-sdk.sh

dev:
	bash ./dev.sh

format:
	black -l 80 ./src app.py wsgi.py

lint:
	flake8 --count ./src app.py wsgi.py

qa:
	make lint
	make test-cov

test:
	python3 -m pytest ./tests

test-cov:
	coverage run --source=./src -m pytest ./tests
	coverage report --fail-under=0 ## TODO: Update with real coverage threshold after tests are backfilled

view-test-cov:
	coverage run --source=./src -m pytest ./tests
	coverage html
	open htmlcov/index.html