.PHONY: build
build:
	@rm -rf dist/
	@rm -rf build/
	@poetry build

.PHONY: tests
tests:
	@poetry run pytest -sv tests
