.PHONY:\
	format\
	check\
	install\
	test\

install:
	uv sync

format:
	uv run ruff format ./kkloader ./test
	uv run ruff check --select I --fix ./kkloader ./test

check:
	uv run ruff check --select I ./kkloader ./test
	uv run pytest

test:
	uv run pytest
