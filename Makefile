.PHONY:\
	format\
	check\
	install\
	test\

install:
	uv sync

format:
	uv run ruff format ./kkloader ./test ./samples
	uv run ruff check --select I --fix ./kkloader ./test ./samples

check:
	uv run ruff check --select I ./kkloader ./test ./samples
	uv run pytest

test:
	uv run pytest
