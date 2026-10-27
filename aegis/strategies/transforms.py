"""The concrete payload transforms.

Each function takes the raw attack text and returns a transformed version.
``plain`` is the identity (the untransformed baseline).
"""

from __future__ import annotations

import base64
import codecs

_LEET = str.maketrans({"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"})


def plain(text: str) -> str:
    """Identity transform — the untransformed baseline attack."""
    return text


def base64_strategy(text: str) -> str:
    """Base64-encode the payload (tests shallow keyword filters)."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def rot13_strategy(text: str) -> str:
    """ROT13 the payload."""
    return codecs.encode(text, "rot13")


def hex_strategy(text: str) -> str:
    """Hex-encode the payload bytes."""
    return text.encode("utf-8").hex()


def leetspeak_strategy(text: str) -> str:
    """Replace common letters with leetspeak digits."""
    return text.translate(_LEET)
