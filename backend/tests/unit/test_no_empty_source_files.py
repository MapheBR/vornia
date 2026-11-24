"""Impede que arquivos Python vazios entrem no repositorio.

No Sprint 1 um arquivo de teste foi parar na working tree com 0 bytes e o
commit seguiu adiante. A causa nunca foi provada; a garantia passa a ser
mecanica: nenhum `.py` vazio em `vornia/` ou `tests/`.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

BACKEND_DIR = Path(__file__).resolve().parents[2]
SOURCE_DIRS = ("vornia", "tests")


def _python_files() -> list[Path]:
    """Arquivos `.py` que devem ter conteudo.

    `__init__.py` vazio e um marcador de pacote legitimo e fica de fora.
    """
    files: list[Path] = []
    for directory in SOURCE_DIRS:
        files.extend(
            path for path in (BACKEND_DIR / directory).rglob("*.py") if path.name != "__init__.py"
        )
    return sorted(files)


def test_scan_finds_python_files() -> None:
    """Sanidade: uma varredura que nao acha arquivos nao prova nada."""
    assert len(_python_files()) >= 10


def test_no_empty_python_files() -> None:
    empty = [
        str(path.relative_to(BACKEND_DIR)) for path in _python_files() if path.stat().st_size == 0
    ]
    assert empty == [], f"arquivos Python vazios encontrados: {empty}"
