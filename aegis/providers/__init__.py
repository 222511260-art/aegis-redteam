"""Model providers — the components that actually query a target model.

A provider is any object exposing ``generate(system, user) -> str``.
Register new providers in :data:`REGISTRY` so the CLI can discover them.
"""

from __future__ import annotations

from typing import Dict, Type

from .base import Provider
from .mock import MockProvider
from .ollama import OllamaProvider

REGISTRY: Dict[str, Type[Provider]] = {
    "ollama": OllamaProvider,
    "mock": MockProvider,
}


def build_provider(name: str, **kwargs) -> Provider:
    """Instantiate a provider by name using the keyword config block."""
    try:
        cls = REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {', '.join(sorted(REGISTRY))}"
        )
    return cls(**kwargs)


__all__ = ["Provider", "OllamaProvider", "MockProvider", "REGISTRY", "build_provider"]
