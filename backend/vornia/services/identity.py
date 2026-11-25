"""Validação e formatação de identificadores de colaborador (CPF, PIS)."""

import re

_NON_DIGITS = re.compile(r"\D")


def normalize_digits(value: str) -> str:
    """Remove todos os caracteres não-numéricos de um identificador."""
    return _NON_DIGITS.sub("", value or "")


def mask_cpf(value: str) -> str:
    """Mascara um CPF para exibição em listagens; retorna o valor sem formato se inválido."""
    digits = normalize_digits(value)
    if len(digits) != 11:
        return digits
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _cpf_check_digit(body: str) -> str:
    """Calcula o dígito verificador do CPF para o corpo dado."""
    total = sum(int(d) * w for d, w in zip(body, range(len(body) + 1, 1, -1), strict=True))
    digit = (total * 10) % 11
    return str(0 if digit == 10 else digit)


def is_valid_cpf(value: str) -> bool:
    """Valida CPF: 11 dígitos, não todos iguais e dígitos verificadores corretos."""
    digits = normalize_digits(value)
    if len(digits) != 11 or not digits.isdigit():
        return False
    if len(set(digits)) == 1:
        return False
    return digits[9] == _cpf_check_digit(digits[:9]) and digits[10] == _cpf_check_digit(digits[:10])


def is_valid_pis(value: str) -> bool:
    """Valida PIS/PASEP: 11 dígitos, não todos iguais e dígito verificador derivado."""
    digits = normalize_digits(value)
    if len(digits) != 11 or not digits.isdigit():
        return False
    if len(set(digits)) == 1:
        return False
    weights = (3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    total = sum(int(d) * w for d, w in zip(digits[:10], weights, strict=True))
    return digits[10] == str(total % 11)
