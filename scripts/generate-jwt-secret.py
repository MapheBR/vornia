"""Generate a secure JWT secret."""

import secrets


def main() -> None:
    secret = secrets.token_hex(32)
    print(secret)


if __name__ == "__main__":
    main()
