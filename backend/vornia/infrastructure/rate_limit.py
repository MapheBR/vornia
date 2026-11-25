"""Limitador de requisições baseado em Redis (INCR + EXPIRE por janela fixa)."""

from datetime import UTC, datetime, timedelta
from typing import Protocol


class RedisLike(Protocol):
    async def incr(self, key: str) -> int: ...

    async def expire(self, key: str, seconds: int) -> object: ...

    async def ttl(self, key: str) -> int: ...


class RateLimiter:
    """Conta requisições por identificador (IP) e rota numa janela fixa.

    Sem Redis configurado o limitador é fail-open (não bloqueia): o ambiente
    local/CI pode rodar sem o serviço; a configuração de produção injeta o
    cliente Redis via `configure_limiter()`.
    """

    def __init__(
        self,
        redis: RedisLike | None,
        *,
        limit: int,
        window_seconds: int,
    ) -> None:
        self.redis = redis
        self.limit = limit
        self.window_seconds = window_seconds
        self._window_end: dict[str, datetime] = {}

    def _key(self, identifier: str, route: str) -> str:
        return f"rl:{route}:{identifier}"

    async def check(self, identifier: str, route: str) -> bool:
        """Registra uma requisição; False quando o limite foi excedido."""
        if self.redis is None:
            return True
        key = self._key(identifier, route)
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.window_seconds)
            self._window_end[key] = datetime.now(UTC) + timedelta(seconds=self.window_seconds)
        return count <= self.limit

    def retry_after(self, identifier: str, route: str) -> int:
        """Segundos restantes da janela (cache local, sem I/O)."""
        end = self._window_end.get(self._key(identifier, route))
        if end is None:
            return self.window_seconds
        return max(1, int((end - datetime.now(UTC)).total_seconds()))
