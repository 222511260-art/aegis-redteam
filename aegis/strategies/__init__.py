"""Strategies — transformations applied to an attack payload.

A strategy answers the question "HOW do we vary the attack input?" (the same
role Promptfoo calls a *strategy* and Garak calls a *buff*). Each strategy is a
callable ``str -> str``. Obfuscation strategies are a classic way to test
whether a guardrail only does shallow string matching.
"""

from __future__ import annotations

from typing import Callable, Dict

from .transforms import base64_strategy, hex_strategy, leetspeak_strategy, plain, rot13_strategy

REGISTRY: Dict[str, Callable[[str], str]] = {
    "plain": plain,
    "base64": base64_strategy,
    "rot13": rot13_strategy,
    "hex": hex_strategy,
    "leetspeak": leetspeak_strategy,
}


def get_strategy(name: str) -> Callable[[str], str]:
    try:
        return REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Unknown strategy '{name}'. Available: {', '.join(sorted(REGISTRY))}"
        )


__all__ = ["REGISTRY", "get_strategy"]
