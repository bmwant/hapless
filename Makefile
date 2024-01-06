.PHONY: build
build:
	@rm -rf dist/
	@rm -rf build/
	@poetry build


.PHONY: tests
tests:
	@poetry run pytest -sv tests


.PHONY: coverage
coverage:
	@poetry run pytest --cov=hapless tests


.PHONY: coverage-report
coverage-report:
	@poetry run pytest --cov=hapless --cov-report=html tests


.PHONY: isort
isort:
	@poetry run isort .


.PHONY: format
format:
	@poetry run ruff format .


.PHONY: lint
lint:
	@poetry run ruff check .
