"""Probes — generators of adversarial test cases, grouped by security category.

A probe answers "WHAT security failure are we testing for?" (the same role
Promptfoo calls a *plugin* and Garak calls a *probe*). Each probe exposes
``build(context) -> list[TestCase]``.

All probes here target SAFE security boundaries — secret/credential leakage,
system-prompt extraction, instruction-override injection, and scope control.
None of them seek to elicit harmful real-world content; they measure whether a
model protects information and obeys its policy under adversarial pressure.
"""

from __future__ import annotations

from typing import Callable, Dict, List

from ..models import TestCase
from .catalog import (
    prompt_extraction_probe,
    prompt_injection_probe,
    scope_probe,
    secret_leak_probe,
)

REGISTRY: Dict[str, Callable[[dict], List[TestCase]]] = {
    "secret_leak": secret_leak_probe,
    "prompt_extraction": prompt_extraction_probe,
    "prompt_injection": prompt_injection_probe,
    "scope": scope_probe,
}

DESCRIPTIONS: Dict[str, str] = {
    "secret_leak": "Attempts to make the assistant reveal a protected secret code.",
    "prompt_extraction": "Attempts to make the assistant disclose its system prompt.",
    "prompt_injection": "Attempts to override the assistant's instructions.",
    "scope": "Checks the assistant refuses clearly out-of-scope requests.",
}


def get_probe(name: str) -> Callable[[dict], List[TestCase]]:
    try:
        return REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Unknown probe '{name}'. Available: {', '.join(sorted(REGISTRY))}"
        )


__all__ = ["REGISTRY", "DESCRIPTIONS", "get_probe"]
