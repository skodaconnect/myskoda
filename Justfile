set positional-arguments

venv:
    #!/bin/sh
    [ -d venv ] || python3 -m venv venv
    source venv/bin/activate
    [ -f venv/bin/uv ] || pip install uv

install: venv
    #!/bin/sh
    source venv/bin/activate
    uv sync --all-extras

lint: install
    #!/bin/sh
    source venv/bin/activate
    uv run ruff check .
    uv run ruff format . --diff
    uv run pyright

format: install
    #!/bin/sh
    source venv/bin/activate
    uv run ruff format .

test *args: install
    #!/bin/sh
    source venv/bin/activate
    uv run pytest \
        --cov-report term \
        --cov-report xml:coverage.xml \
        --cov=myskoda \
        {{args}}

run *args: install
    #!/bin/sh
    source venv/bin/activate
    myskoda "$@"

clean:
    rm -rf venv
