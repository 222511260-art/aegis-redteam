"""Aegis — a local-first LLM security evaluation toolkit.

Aegis is a small, modular red-teaming harness inspired by Promptfoo and Garak.
It sends adversarial *test cases* to a target model, transforms them with
*strategies*, grades the responses with *detectors*, and reports an
Attack Success Rate (ASR) broken down by security category.

All evaluation runs entirely against a LOCAL model (Ollama) or an offline
mock provider. No data leaves the machine.
"""

__version__ = "1.0.0"
__all__ = ["__version__"]
