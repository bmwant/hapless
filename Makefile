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


.PHONY: format
format:
	@poetry run ruff format .


.PHONY: lint
lint:
	@poetry run ruff check .


.PHONY: tag
tag:
	@VERSION=$$(poetry version --short); \
	git tag -a "v$$VERSION" -m "Version $$VERSION"; \
	git push origin "v$$VERSION"; \
	echo "Created and pushed tag v$$VERSION"
