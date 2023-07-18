lint:
	flake8 --count ./src app.py wsgi.py

format:
	black -l 80 ./src app.py wsgi.py