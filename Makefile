install:
	poetry install
	poetry run pre-commit install

dev:
	poetry run flet run washer/main.py

dev-ios:
	poetry run flet run washer/main.py --ios --port 8552

dev-android:
	poetry run flet run washer/main.py --android --port 8552

lint:
	poetry run ruff check

lint_fix:
	poetry run ruff check --fix

format:
	poetry run ruff format
