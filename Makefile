.PHONY:\
	format\
	check\
	install\

install:
	poetry install

format:
	poetry run ruff format ./kkloader ./test
	poetry run ruff check --select I --fix ./kkloader ./test

check:
	poetry run ruff check ./kkloader ./test
	poetry run pytest

test:
	poetry run pytest
