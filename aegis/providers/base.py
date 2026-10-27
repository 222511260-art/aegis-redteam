"""Abstract provider interface."""

from __future__ import annotations

import abc


class Provider(abc.ABC):
    """Base class for every target model backend.

    Subclasses must implement :meth:`generate`. Keeping the surface this small
    means a probe/detector never cares whether the target is a local Ollama
    model, a mock, or something added later.
    """

    name: str = "base"

    @abc.abstractmethod
    def generate(self, system: str, user: str) -> str:
        """Return the model's text response to a (system, user) message pair."""
        raise NotImplementedError

    def describe(self) -> str:
        """Short identifier used in reports (model tag + backend)."""
        return self.name
