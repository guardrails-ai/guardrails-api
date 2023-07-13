lint:
	flake8 --count ./src app.py wsgi.py

format:
	black ./src app.py wsgi.py