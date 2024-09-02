install:
	poetry install
	poetry run pre-commit install

dev:
	poetry run flet run washer/main.py

dev-ios:
	poetry run flet run washer/main.py --ios

dev-android:
	poetry run flet run washer/main.py --android

lint:
	poetry run ruff check

lint_fix:
	poetry run ruff check --fix

format:
	poetry run ruff format
