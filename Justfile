lint:
    poetry run ruff check .
    poetry run ruff format . --diff
    poetry run pyright

format:
    poetry run ruff format .

test:
    poetry run pytest \
        --cov-report term \
        --cov-report xml:coverage.xml \
        --cov=myskoda