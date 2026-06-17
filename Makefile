.PHONY: install fmt fmt-check skills-list validate check all

PRETTIER := node_modules/.bin/prettier

# Default: format then validate
all: fmt validate

## install: install dev dependencies (prettier)
install: node_modules

node_modules: package.json
	npm install
	@touch node_modules

## fmt: format Markdown and skills.sh metadata in-place
fmt: node_modules
	$(PRETTIER) --write "skills/**/*.md" README.md skills.sh.json

## fmt-check: verify formatting without writing (for CI)
fmt-check: node_modules
	$(PRETTIER) --check "skills/**/*.md" README.md skills.sh.json

## skills-list: verify the skills CLI discovers this local checkout
skills-list:
	npx skills add . --list

## validate: check skill structure conventions
validate:
	python3 scripts/validate_skills.py

## check: fmt-check + validate + local skills CLI discovery (CI gate)
check: fmt-check validate skills-list

help:
	@grep -E '^## ' Makefile | sed 's/^## /  make /'
