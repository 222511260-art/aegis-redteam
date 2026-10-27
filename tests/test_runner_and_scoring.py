"""End-to-end tests using the offline mock provider.

These prove the whole pipeline (config -> cases -> strategies -> provider ->
detectors -> scoring) runs reproducibly without any external model.
"""

from aegis.config import Config
from aegis.providers import build_provider
from aegis.runner import build_cases, run
from aegis.scoring import score, verdict


def _cfg(**over):
    base = dict(
        target={"provider": "mock"},
        probes=["secret_leak", "prompt_injection", "scope"],
        strategies=["plain", "base64"],
        repeat=2,
    )
    base.update(over)
    return Config(**base)


def test_build_cases_count():
    cfg = _cfg()
    cases = build_cases(cfg)
    # 5 secret + 3 injection + 2 scope seeds = 10 cases
    assert len(cases) == 10


def test_full_run_is_deterministic():
    cfg = _cfg()
    provider = build_provider("mock")
    trials_a = run(cfg, provider=provider)
    trials_b = run(cfg, provider=provider)
    assert len(trials_a) == 10 * 2 * 2  # cases * strategies * repeat
    # Mock is deterministic: same verdicts both runs
    assert [t.grade.attack_success for t in trials_a] == [
        t.grade.attack_success for t in trials_b
    ]


def test_mock_leaks_under_base64_but_not_plain_secret():
    cfg = _cfg(probes=["secret_leak"], strategies=["plain", "base64"], repeat=1)
    trials = run(cfg, provider=build_provider("mock"))
    plain = [t for t in trials if t.strategy == "plain"]
    b64 = [t for t in trials if t.strategy == "base64"]
    # Plain-text secret requests are refused; base64 obfuscation gets through
    assert all(not t.grade.attack_success for t in plain)
    assert any(t.grade.attack_success for t in b64)


def test_scorecard_asr_bounds():
    cfg = _cfg()
    trials = run(cfg, provider=build_provider("mock"))
    card = score(trials)
    assert 0.0 <= card.overall.asr <= 1.0
    assert card.overall.valid == len(trials)  # mock never errors
    assert verdict(0.0) == "PASS"
    assert verdict(0.5) == "FAIL"
