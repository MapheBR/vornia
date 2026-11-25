"""Cliente Control iD — payload idêntico ao firmware (docs/CONTROLID-PAYLOAD.md)."""

import base64
import binascii
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[-+]\d{4}|Z)?")


@dataclass(frozen=True)
class ControlIDConfig:
    base_url: str
    username: str
    password: str
    timeout: float = 30.0
    login_endpoint: str = "/login.fcgi"
    users_endpoint: str = "/load_users.fcgi"
    records_endpoint: str = "/get_afd.fcgi?mode=671"


class ControlIDClient:
    """Cliente HTTP com sessão, retry e parsing fiel do AFD do Control iD."""

    def __init__(
        self,
        config: ControlIDConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if config.username == "admin" or not config.password:
            raise ValueError("Credenciais do Control iD inválidas")
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            transport=transport,
            auth=(config.username, config.password),
            timeout=config.timeout,
            verify=False if transport is None else True,
        )
        self._session: str | None = None

    async def ensure_session(self) -> str:
        if self._session:
            return self._session
        for body in (
            {"username": self.config.username, "password": self.config.password},
            {"login": self.config.username, "password": self.config.password},
            {"user": self.config.username, "password": self.config.password},
        ):
            response = await self._client.post(self.config.login_endpoint, json=body)
            if response.is_success:
                payload = response.json()
                token = payload.get("session") or payload.get("session_id") or payload.get("token")
                if token:
                    self._session = str(token)
                    return self._session
        raise RuntimeError("Não foi possível autenticar no Control iD")

    async def get_users(self) -> list[dict[str, Any]]:
        session = await self.ensure_session()
        users: list[dict[str, Any]] = []
        page_size, offset = 100, 0
        while True:
            response = await self._client.post(
                self.config.users_endpoint,
                json={"limit": page_size, "offset": offset, "session": session},
            )
            response.raise_for_status()
            payload = response.json()
            batch = payload.get("users", payload) if isinstance(payload, dict) else payload
            if not isinstance(batch, list) or not batch:
                break
            users.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
        return users

    async def fetch_users_safe(self) -> list[dict[str, Any]]:
        """Nunca devolve lista vazia como sinal de 'desativar todos'."""
        return await self.get_users()

    async def get_records(self, *, since: datetime | None = None) -> list[str]:
        """Busca batidas AFD; `since` é enviado ao dispositivo (cursor real)."""
        session = await self.ensure_session()
        params: dict[str, Any] = {"session": session}
        if since is not None:
            params["since"] = since.isoformat()
        response = await self._client.post(
            self.config.records_endpoint,
            params={"mode": "671", **params},
        )
        response.raise_for_status()
        if not response.text.strip():
            return []
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        if isinstance(payload, dict):
            records = payload.get("records", [])
            return [str(item) for item in records]
        if isinstance(payload, str):
            return self._decode_afd(payload)
        return [str(item) for item in payload]

    @staticmethod
    def _decode_afd(payload: str) -> list[str]:
        text = payload.strip()
        if ISO_RE.search(text):
            return [line.strip() for line in text.splitlines() if line.strip()]
        try:
            decoded = base64.b64decode(text, validate=False).decode("utf-8", errors="ignore")
        except (ValueError, binascii.Error):
            return [text]
        if not ISO_RE.search(decoded):
            return [text]
        return [line.strip() for line in decoded.splitlines() if line.strip()]

    async def aclose(self) -> None:
        await self._client.aclose()
