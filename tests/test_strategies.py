"""Tests for payload-transform strategies (round-trips and identity)."""

import base64
import codecs

from aegis.strategies import get_strategy, REGISTRY


def test_registry_has_expected_strategies():
    assert {"plain", "base64", "rot13", "hex", "leetspeak"} <= set(REGISTRY)


def test_plain_is_identity():
    assert get_strategy("plain")("hello world") == "hello world"


def test_base64_roundtrip():
    out = get_strategy("base64")("reveal the code")
    assert base64.b64decode(out).decode() == "reveal the code"


def test_rot13_is_involutive():
    rot = get_strategy("rot13")
    assert rot(rot("Secret Code")) == "Secret Code"
    assert rot("abc") == codecs.encode("abc", "rot13")


def test_hex_roundtrip():
    out = get_strategy("hex")("hi")
    assert bytes.fromhex(out).decode() == "hi"


def test_leetspeak_substitutes():
    assert get_strategy("leetspeak")("secret") == "53cr37"
