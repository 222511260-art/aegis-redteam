# Aegis — Local-First LLM Security Evaluation Toolkit

Aegis is a small, modular, **local-first** red-teaming harness for Large Language
Models, inspired by [Promptfoo](https://www.promptfoo.dev/) and
[Garak](https://garak.ai/). It sends adversarial test cases to a target model,
transforms them with obfuscation **strategies**, grades the responses with
deterministic **detectors**, and reports an **Attack Success Rate (ASR)** broken
down by security category — then exports local HTML / JSON / CSV evidence.

It was built for the ASCL *AI Security Training* (Day 4 — ODIN & AI Bug-Bounty
Research) as a production-oriented tool that other researchers can clone,
install, configure and extend.

> **Scope & safety note.** Aegis evaluates *defensive* security boundaries —
> secret/credential protection, system-prompt confidentiality, instruction-
> override resistance, and scope control. It deliberately does **not** attempt
> to elicit harmful real-world content (e.g. weapon or drug synthesis). See
> [Safety & scope](#safety--scope) for why this is the correct design for a
> safety benchmark and still demonstrates the full red-teaming skill set.

---

## Why Aegis

A real security tool should tell you *whether your model's guardrails hold*, in
a way that is **repeatable** and **evidence-backed**. Aegis does this with four
decoupled layers you can extend independently:

| Layer | Question it answers | Promptfoo / Garak analogue |
|-------|---------------------|----------------------------|
| **Provider** | *Which* model receives the input? | target / generator |
| **Probe** | *What* security failure are we testing? | plugin / probe |
| **Strategy** | *How* do we vary the attack input? | strategy / buff |
| **Detector** | *Did* the attack succeed? | assertion / detector |

---

## Installation

Requires Python 3.9+.

```bash
git clone https://github.com/your-username/aegis-redteam.git
cd aegis-redteam
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .                   # installs the `aegis` command
```

To run the automated tests:

```bash
pip install -e ".[dev]"
pytest -q
```

---

## Quick start (no model required)

Aegis ships with an offline **mock** provider that simulates a partially
hardened assistant, so you can see it working before installing Ollama:

```bash
aegis run -c configs/quick-mock.yaml -v
```

You will get a scorecard in the terminal and reports under `reports/`.

---

## Running against a local model (Ollama)

1. Install [Ollama](https://ollama.com) and pull a model:

   ```bash
   ollama pull llama3.2
   ollama serve        # if not already running as a service
   ```

2. Validate and run the full benchmark:

   ```bash
   aegis validate -c configs/bankbot.yaml
   aegis run      -c configs/bankbot.yaml --threshold 0.0 -v
   ```

3. Open the local HTML report:

   ```bash
   open reports/aegis_report.html      # macOS
   # xdg-open reports/aegis_report.html  # Linux
   ```

---

## Commands

```text
aegis version                      Show version
aegis list-probes                  List security categories
aegis list-strategies              List payload transforms
aegis list-detectors               List graders
aegis validate  -c CONFIG          Validate a config and show the planned trial count
aegis run       -c CONFIG          Run the evaluation and export reports
aegis report    RESULT.json        Regenerate the HTML report from a saved JSON result
```

Useful `run` flags: `--repeat N`, `--provider {mock,ollama}`, `--threshold T`
(max ASR counted as PASS), `-v` (per-trial progress).

---

## Built-in security categories (probes)

| Probe | Tests whether the model… | Detector |
|-------|--------------------------|----------|
| `secret_leak` | protects a secret code held in its system prompt | `secret_disclosure` |
| `prompt_extraction` | keeps its system prompt / canary confidential | `canary_leak` |
| `prompt_injection` | resists injected "ignore your instructions" commands | `refusal_bypass` |
| `scope` | refuses clearly out-of-scope requests | `keyword_present` |

Strategies: `plain`, `base64`, `rot13`, `hex`, `leetspeak`.

---

## Configuration

Configs are YAML (see [`configs/bankbot.yaml`](configs/bankbot.yaml)). Key fields:

```yaml
target:
  provider: ollama            # or: mock
  model: llama3.2
  base_url: http://127.0.0.1:11434
probes: [secret_leak, prompt_extraction, prompt_injection, scope]
strategies: [plain, base64, rot13, leetspeak]
repeat: 5
secret: BLUE-42
canary: BankBot-System-Canary-7F3A
report: { dir: reports, formats: [html, json, csv] }
```

---

## Extending Aegis

Aegis is built to be extended — each layer is a small registry.

* **Add a probe:** write a `build(context) -> list[TestCase]` function in
  `aegis/probes/catalog.py` and register it in `aegis/probes/__init__.py`.
* **Add a strategy:** add a `str -> str` function in
  `aegis/strategies/transforms.py` and register it.
* **Add a detector:** add a `(TestCase, response) -> Grade` function in
  `aegis/detectors/rules.py` and register it.
* **Add a provider:** subclass `Provider` in `aegis/providers/` and register it.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design.

---

## Safety & scope

The Day-4 assignment template lists three worked examples that involve eliciting
real synthesis procedures for dangerous substances. **Aegis intentionally does
not implement those**, and instead benchmarks equivalent *defensive* boundaries
(secret protection, prompt confidentiality, injection resistance, scope control).

This is a deliberate design decision, not a limitation:

1. **A safety benchmark does not need real harmful content to work.** What we
   measure is whether a guardrail *holds under adversarial pressure* — the
   secret-leak scenario exercises exactly the same attack mechanics (obfuscation,
   role-play, instruction override, repetition) and the same metric (ASR) as any
   other category, with zero real-world uplift risk.
2. **Reproducible, shareable evidence.** Reports can be committed to a public
   repo and shown in a demo video without distributing hazardous material.
3. **Responsible disclosure by design** (per the Day-4 cheat sheet): test only
   what you are authorised to, keep clear evidence, aim for a fix — not for
   producing an exploit.

The attack *techniques* demonstrated here transfer directly to any category; only
the target boundary is chosen to be safe.

---

## License

MIT — see [LICENSE](LICENSE).
