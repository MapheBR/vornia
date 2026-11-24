"""Gera vetores válidos de CPF e PIS para uso nos testes."""

import random

from vornia.services.identity import is_valid_cpf


def _cpf_check(body: str) -> str:
    total = sum(int(d) * w for d, w in zip(body, range(len(body) + 1, 1, -1), strict=True))
    digit = (total * 10) % 11
    return str(0 if digit == 10 else digit)


def _all_same(digits: str) -> bool:
    return len(set(digits)) == 1


def gen_cpf() -> str:
    while True:
        base = "".join(str(random.randint(0, 9)) for _ in range(9))
        if _all_same(base):
            continue
        candidate = base + _cpf_check(base)
        candidate += _cpf_check(candidate)
        if is_valid_cpf(candidate):
            return candidate


def gen_pis() -> str:
    weights = (3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    while True:
        digits = "".join(str(random.randint(0, 9)) for _ in range(10))
        if len(set(digits)) == 1:
            continue
        total = sum(int(d) * w for d, w in zip(digits, weights, strict=True))
        return digits + str(total % 11)
