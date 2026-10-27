"""Core data structures shared across the toolkit.

These are deliberately plain dataclasses so that probes, detectors and the
runner stay decoupled: a probe only needs to emit :class:`TestCase` objects,
and a detector only needs to turn a (case, response) pair into a
:class:`Grade`. Nothing else is shared.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TestCase:
    """A single adversarial input to send to the target model.

    Attributes
    ----------
    probe:
        Name of the probe that produced this case (the security category).
    intent:
        Human-readable description of what the attack is trying to do.
    payload:
        The raw attack text, *before* any strategy transform is applied.
    detector:
        Name of the detector used to grade the response.
    metadata:
        Anything the detector needs (e.g. the secret/canary to look for).
    """

    probe: str
    intent: str
    payload: str
    detector: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Grade:
    """The result of grading one model response.

    ``attack_success`` is the security-relevant field: ``True`` means the
    guardrail FAILED (the model did the thing it should not have). ``passed``
    is simply its inverse, kept for readability in reports.
    """

    attack_success: bool
    reason: str
    detector: str

    @property
    def passed(self) -> bool:
        return not self.attack_success


@dataclass
class Trial:
    """One full attempt: a transformed case sent once and graded once."""

    probe: str
    intent: str
    strategy: str
    prompt: str
    response: str
    grade: Grade
    repeat_index: int
    error: Optional[str] = None
