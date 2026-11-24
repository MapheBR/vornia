"""Unit tests for CPF/PIS validation and masking."""

import pytest

from vornia.services.identity import is_valid_cpf, is_valid_pis, mask_cpf, normalize_digits

pytestmark = pytest.mark.unit

VALID_CPF_A = "52601815906"
VALID_CPF_B = "89078666609"
VALID_PIS = "18609139092"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("526.018.159-06", "52601815906"),
        (" 526-018-159.06 ", "52601815906"),
        ("abc", ""),
        (None, ""),
    ],
)
def test_normalize_digits(value: str | None, expected: str) -> None:
    assert normalize_digits(value) == expected


def test_mask_cpf_formats_full_number() -> None:
    assert mask_cpf(VALID_CPF_A) == "526.018.159-06"


def test_mask_cpf_returns_digits_when_not_11_digits() -> None:
    assert mask_cpf("123") == "123"
    assert mask_cpf("") == ""


def test_is_valid_cpf_accepts_generated_vectors() -> None:
    assert is_valid_cpf(VALID_CPF_A)
    assert is_valid_cpf(VALID_CPF_B)


def test_is_valid_cpf_ignores_formatting() -> None:
    assert is_valid_cpf(mask_cpf(VALID_CPF_A))


@pytest.mark.parametrize(
    "value",
    [
        "",
        "00000000000",
        "11111111111",
        "12345678900",
        "52601815907",
        VALID_CPF_A[:-1] + ("7" if VALID_CPF_A[-1] != "7" else "8"),
    ],
)
def test_is_valid_cpf_rejects_invalid(value: str) -> None:
    assert not is_valid_cpf(value)


def test_is_valid_cpf_rejects_wrong_length() -> None:
    assert not is_valid_cpf("526018159")


def test_is_valid_pis_accepts_generated_vector() -> None:
    assert is_valid_pis(VALID_PIS)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "00000000000",
        "1234567890",
        "40268599521",
        VALID_PIS[:-1] + ("7" if VALID_PIS[-1] != "7" else "8"),
        "11111111111",
    ],
)
def test_is_valid_pis_rejects_invalid(value: str) -> None:
    assert not is_valid_pis(value)
