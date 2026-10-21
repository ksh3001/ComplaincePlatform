set shell := ["bash", "-cu"]

up:
    docker compose up -d --build

migrate:
    docker compose exec api alembic upgrade head

test:
    cd backend && uv run pytest
    cd frontend && pnpm test

lint:
    cd backend && uv run ruff check . && uv run mypy
    cd frontend && pnpm lint && pnpm exec tsc -b

gen-client:
    @echo "stub: implemented in a later task"

eval:
    @echo "stub: implemented in a later task"
