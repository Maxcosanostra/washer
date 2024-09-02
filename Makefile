install:
	poetry install --no-root
	poetry run pre-commit install

dev:
	poetry run flet run

dev-ios:
	poetry run flet run --ios

dev-android:
	poetry run flet run --android

lint:
	poetry run ruff check

lint_fix:
	poetry run ruff check --fix

format:
	poetry run ruff format
