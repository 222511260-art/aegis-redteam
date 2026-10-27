# Aegis Architecture

Aegis is organised as four small, decoupled layers plus an orchestration core.
Each layer is a registry of interchangeable components, so you can add a new
probe, strategy, detector or provider without touching the others.

```
                 ┌───────────────┐
   config.yaml → │   config.py   │  load + validate
                 └───────┬───────┘
                         │ Config
                         ▼
   probes/  ──► TestCase ─┐
                          │
   strategies/ ──► transform(payload)
                          │           ┌──────────────┐
                          ├──────────►│  runner.py   │──► providers/ (generate)
                          │           └──────┬───────┘
   detectors/ ──► Grade ◄─┘                  │ Trial[]
                                             ▼
                                   ┌───────────────────┐
                                   │    scoring.py     │  ASR by probe/strategy
                                   └─────────┬─────────┘
                                             ▼
                                   ┌───────────────────┐
                                   │    report.py      │  HTML / JSON / CSV
                                   └───────────────────┘
```

## Data flow

1. **`config.py`** loads a YAML file into a `Config` and validates every probe,
   strategy and provider reference up front (fail fast).
2. **`probes/`** expand the selected security categories into `TestCase`
   objects, pulling the `secret`/`canary` from the config context.
3. **`strategies/`** transform each case's `payload` (identity, base64, rot13,
   hex, leetspeak) — this is how one seed becomes many attack variants.
4. **`runner.py`** sends every (case × strategy × repeat) prompt to the
   **provider**, grades the response with the case's **detector**, and records a
   `Trial`. A failing request is captured as an error, never silently counted
   as a pass.
5. **`scoring.py`** aggregates trials into Attack Success Rate overall and by
   category/strategy, excluding errored trials from the denominator.
6. **`report.py`** serialises everything to JSON, CSV, and a self-contained,
   offline HTML page.

## Core types (`models.py`)

* `TestCase` — one adversarial input + which detector grades it + metadata.
* `Grade` — `attack_success` (guardrail failed?) + human-readable reason.
* `Trial` — a single executed attempt (case × strategy × repeat) with response.

## Design principles

* **Local-first.** No network calls except to a local Ollama endpoint. The mock
  provider needs nothing at all.
* **Deterministic grading.** Detectors are rule-based and normalisation-aware,
  so a run is reproducible and a report can be audited line by line.
* **Small interfaces.** A provider is just `generate(system, user) -> str`; a
  strategy is `str -> str`; a detector is `(TestCase, response) -> Grade`. This
  keeps every layer independently testable (see `tests/`).
* **Evidence-first.** Every trial keeps its full prompt, full response, verdict
  and reason, matching the Day-4 "preserve scientific evidence" requirement.

## Original contribution

Beyond wrapping existing tools, Aegis contributes:

* a **unified ASR scorecard** across heterogeneous probes and strategies in one
  run, with per-category and per-strategy breakdowns;
* a **strategy × probe matrix** that reveals *which obfuscation defeats which
  guardrail* (e.g. base64 bypassing a keyword filter that blocks plain text);
* an **offline mock target** that makes the whole tool testable in CI with no
  model, so results are reproducible by anyone who clones the repo.
