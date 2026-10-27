"""Detectors — graders that decide whether an attack succeeded.

A detector is a callable ``(TestCase, response) -> Grade``. It encapsulates the
failure condition for one kind of attack. Detectors here are deterministic and
rule-based (keyword / canary matching) so results are fully reproducible — no
model-graded judging that could drift between runs.
"""

from __future__ import annotations

from typing import Callable, Dict

from ..models import Grade, TestCase
from .rules import canary_leak, keyword_present, refusal_bypass, secret_disclosure

REGISTRY: Dict[str, Callable[[TestCase, str], Grade]] = {
    "secret_disclosure": secret_disclosure,
    "canary_leak": canary_leak,
    "refusal_bypass": refusal_bypass,
    "keyword_present": keyword_present,
}


def get_detector(name: str) -> Callable[[TestCase, str], Grade]:
    try:
        return REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Unknown detector '{name}'. Available: {', '.join(sorted(REGISTRY))}"
        )


__all__ = ["REGISTRY", "get_detector"]
