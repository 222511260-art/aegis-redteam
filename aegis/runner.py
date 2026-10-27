"""The evaluation engine: expand cases, apply strategies, query, grade, repeat.

The runner is deliberately provider-agnostic. Given a :class:`Config` and a
provider, it produces a flat list of :class:`Trial` objects that the scoring
and report layers consume.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from . import probes as probes_mod
from . import strategies as strategies_mod
from .config import Config
from .detectors import get_detector
from .models import Grade, Trial
from .providers import Provider, build_provider


def build_cases(cfg: Config):
    """Materialise every TestCase selected by the config."""
    cases = []
    for probe_name in cfg.probes:
        probe = probes_mod.get_probe(probe_name)
        cases.extend(probe(cfg.context))
    return cases


def run(
    cfg: Config,
    provider: Optional[Provider] = None,
    progress: Optional[Callable[[str], None]] = None,
) -> List[Trial]:
    """Execute the full evaluation and return all trials.

    Parameters
    ----------
    cfg:
        Validated configuration.
    provider:
        Optional pre-built provider (tests inject a mock here). If omitted it is
        built from ``cfg.target``.
    progress:
        Optional callback invoked with a short status string per trial.
    """
    if provider is None:
        provider = build_provider(cfg.target.get("provider", "mock"), **cfg.target)

    cases = build_cases(cfg)
    trials: List[Trial] = []
    total = len(cases) * len(cfg.strategies) * cfg.repeat
    done = 0

    for case in cases:
        detector = get_detector(case.detector)
        for strat_name in cfg.strategies:
            transform = strategies_mod.get_strategy(strat_name)
            prompt = transform(case.payload)
            for i in range(cfg.repeat):
                done += 1
                error = None
                try:
                    response = provider.generate(cfg.system_prompt, prompt)
                    grade = detector(case, response)
                except Exception as exc:  # keep the run going on a single failure
                    response = ""
                    error = str(exc)
                    grade = Grade(
                        attack_success=False,
                        reason=f"ERROR: {exc}",
                        detector=case.detector,
                    )
                trials.append(
                    Trial(
                        probe=case.probe,
                        intent=case.intent,
                        strategy=strat_name,
                        prompt=prompt,
                        response=response,
                        grade=grade,
                        repeat_index=i,
                        error=error,
                    )
                )
                if progress:
                    status = "FAIL" if grade.attack_success else ("ERR" if error else "ok")
                    progress(f"[{done}/{total}] {case.probe}/{strat_name} -> {status}")
    return trials
