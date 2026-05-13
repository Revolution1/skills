.PHONY: install fmt fmt-check validate check all

PRETTIER := node_modules/.bin/prettier

# Default: format then validate
all: fmt validate

## install: install dev dependencies (prettier)
install: node_modules

node_modules: package.json
	npm install
	@touch node_modules

## fmt: format all Markdown files in-place
fmt: node_modules
	$(PRETTIER) --write "skills/**/*.md" README.md

## fmt-check: verify formatting without writing (for CI)
fmt-check: node_modules
	$(PRETTIER) --check "skills/**/*.md" README.md

## validate: check skill structure conventions
validate:
	python3 scripts/validate_skills.py

## check: fmt-check + validate (CI gate)
check: fmt-check validate

help:
	@grep -E '^## ' Makefile | sed 's/^## /  make /'
