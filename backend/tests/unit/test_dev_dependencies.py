"""Garante que o ambiente de desenvolvimento declarado esta completo.

O venv local ja foi populado sem `pip-audit` no Sprint 1, mesmo com a
dependencia declarada. Este teste trava a declaracao: se uma ferramenta
obrigatoria sair do extra `dev`, o CI falha antes de alguem descobrir em
tempo de execucao.
"""

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"

REQUIRED_DEV_TOOLS = (
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "ruff",
    "mypy",
    "bandit",
    "pip-audit",
)


def _requirement_name(requirement: str) -> str:
    """Extrai o nome do pacote de uma linha de dependencia PEP 508."""
    name = requirement.split(";")[0]
    for separator in ("[", ">", "<", "=", "!", "~", " "):
        name = name.split(separator)[0]
    return name.strip().lower()


def _dev_extras() -> list[str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    extras: list[str] = data["project"]["optional-dependencies"]["dev"]
    return extras


@pytest.mark.parametrize("tool", REQUIRED_DEV_TOOLS)
def test_dev_extra_declares_tool(tool: str) -> None:
    declared = {_requirement_name(item) for item in _dev_extras()}
    assert (
        tool in declared
    ), f"{tool} ausente em [project.optional-dependencies].dev do pyproject.toml"
