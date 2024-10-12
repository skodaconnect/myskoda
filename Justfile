set positional-arguments

venv:
    #!/bin/sh
    [ -d venv ] || python3 -m venv venv
    source venv/bin/activate
    [ -f venv/bin/poetry ] || pip install poetry

install: venv
    #!/bin/sh
    source venv/bin/activate
    poetry install --quiet --all-extras

lint: install
    #!/bin/sh
    source venv/bin/activate
    poetry run ruff check .
    poetry run ruff format . --diff
    poetry run pyright

format: install
    #!/bin/sh
    source venv/bin/activate
    poetry run ruff format .

test *args: install
    #!/bin/sh
    source venv/bin/activate
    poetry run pytest \
        --cov-report term \
        --cov-report xml:coverage.xml \
        --cov=myskoda \
        {{args}}

run *args: install
    #!/bin/sh
    source venv/bin/activate
    myskoda {{args}}

clean:
    rm -rf venv

gen-fixtures +args: install
    #!/bin/sh
    source venv/bin/activate
    python scripts/gen_fixtures.py "$@"