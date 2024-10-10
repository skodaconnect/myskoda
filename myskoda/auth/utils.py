"""Utilities for authorization."""

import random
import string


def generate_nonce() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=16))  # noqa: S311
