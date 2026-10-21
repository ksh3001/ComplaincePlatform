from typing import Any

from arq.connections import RedisSettings

from app.config import settings


async def noop(ctx: dict[str, Any]) -> None:
    """Placeholder job so the worker starts; real jobs arrive in later tasks."""


class WorkerSettings:
    functions = [noop]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
