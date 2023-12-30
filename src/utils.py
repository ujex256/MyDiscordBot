import secrets

from discord import Color


def generate_secure_id(n: int) -> int:
    min_value = 10 ** (n - 1)
    max_value = (10 ** n) - 1
    print(max_value)
    secure_id = secrets.randbelow(max_value - min_value + 1) + min_value
    return secure_id


class EmbedColors:
    SUCCESS = Color.blue()
    FAILED = Color.red()
