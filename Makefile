.PHONY:\
	format\
	check\
	install\

install:
	poetry install

format:
	poetry run ruff format ./kkloader ./test

check:
	poetry run ruff check ./kkloader ./test
	poetry run pytest