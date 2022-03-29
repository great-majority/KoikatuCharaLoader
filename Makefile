.PHONY:\
	format\
	check\
	install\

install:
	poetry install

format:
	poetry run isort ./kkloader ./test
	poetry run black ./kkloader ./test

check:
	poetry run flake8 ./kkloader ./test --count --show-source --statistics
	poetry run black ./kkloader ./test --check --diff
	poetry run isort ./kkloader ./test --check-only
	poetry run pytest