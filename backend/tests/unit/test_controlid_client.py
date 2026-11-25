"""Testes do cliente Control iD com payload idêntico ao firmware real.

Fonte: docs/CONTROLID-PAYLOAD.md (extraído de PontoJa/controlid_api.py).
"""

from datetime import UTC, datetime

import httpx
import pytest

pytestmark = pytest.mark.unit

TOKEN = "sessao-123"
# timestamp real: ±HHMM sem dois-pontos; sufixo = zeros + PIS + hash
AFD_LINE = "2026-11-25T08:00:00-03000000123456789012A1B2"
AFD_LINE_2 = "2026-11-25T17:00:00-03000000123456789012C3D4"
USERS_JSON = {"users": [{"id": 12345678901, "nome": "Maria"}]}


def _handler(afd_body: str = f"{AFD_LINE}\n{AFD_LINE_2}\n") -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("login.fcgi"):
            return httpx.Response(200, json={"session": TOKEN})
        if path.endswith("load_users.fcgi"):
            return httpx.Response(200, json=USERS_JSON)
        if path.endswith("get_afd.fcgi"):
            assert request.method == "POST"
            assert request.url.params["mode"] == "671"
            return httpx.Response(200, text=afd_body)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


async def test_login_extracts_session() -> None:
    from vornia.integrations.controlid import ControlIDClient, ControlIDConfig

    client = ControlIDClient(
        ControlIDConfig(base_url="https://device.local", username="u", password="p"),
        transport=_handler(),
    )
    assert await client.ensure_session() == TOKEN


async def test_get_users_paginates_with_limit_offset() -> None:
    from vornia.integrations.controlid import ControlIDClient, ControlIDConfig

    client = ControlIDClient(
        ControlIDConfig(base_url="https://device.local", username="u", password="p"),
        transport=_handler(),
    )
    users = await client.get_users()
    assert users == [{"id": 12345678901, "nome": "Maria"}]


async def test_get_records_parses_afd_text_lines() -> None:
    from vornia.integrations.controlid import ControlIDClient, ControlIDConfig

    client = ControlIDClient(
        ControlIDConfig(base_url="https://device.local", username="u", password="p"),
        transport=_handler(),
    )
    records = await client.get_records(since=datetime(2026, 11, 25, tzinfo=UTC))
    assert records == [AFD_LINE, AFD_LINE_2]


async def test_get_records_accepts_base64() -> None:
    import base64

    from vornia.integrations.controlid import ControlIDClient, ControlIDConfig

    encoded = base64.b64encode(AFD_LINE.encode()).decode()
    client = ControlIDClient(
        ControlIDConfig(base_url="https://device.local", username="u", password="p"),
        transport=_handler(afd_body=encoded),
    )
    assert await client.get_records() == [AFD_LINE]


async def test_empty_user_list_never_disables_everyone() -> None:
    """Defeito #3: lista vazia não pode autorizar desativação em massa."""
    from vornia.integrations.controlid import ControlIDClient, ControlIDConfig

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("login.fcgi"):
            return httpx.Response(200, json={"session": TOKEN})
        return httpx.Response(200, json={"users": []})

    transport = httpx.MockTransport(handler)
    client = ControlIDClient(
        ControlIDConfig(base_url="https://device.local", username="u", password="p"),
        transport=transport,
    )
    assert await client.fetch_users_safe() == []
