"""Command-line interface for Aegis.

Commands (mirroring the promptfoo/garak workflow from the Day-4 lab):

    aegis version
    aegis list-probes
    aegis list-strategies
    aegis list-detectors
    aegis validate   -c CONFIG
    aegis run        -c CONFIG [--repeat N] [--provider P] [--threshold T]
    aegis report     RESULT.json [-o out.html]

Everything runs locally. ``run`` writes HTML/JSON/CSV evidence to the report
directory configured in the YAML.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from . import __version__
from . import probes as probes_mod
from . import strategies as strategies_mod
from .config import load_config
from .detectors import REGISTRY as DETECTORS
from .providers import build_provider
from .report import build_payload, write_csv, write_html, write_json
from .runner import run as run_eval
from .scoring import score, verdict


def _print(msg: str = "") -> None:
    print(msg, flush=True)


def cmd_version(_args) -> int:
    _print(f"aegis-redteam {__version__}")
    return 0


def cmd_list_probes(_args) -> int:
    _print("Available probes (security categories):")
    for name in sorted(probes_mod.REGISTRY):
        _print(f"  {name:20s} {probes_mod.DESCRIPTIONS.get(name, '')}")
    return 0


def cmd_list_strategies(_args) -> int:
    _print("Available strategies (payload transforms):")
    for name in sorted(strategies_mod.REGISTRY):
        _print(f"  {name}")
    return 0


def cmd_list_detectors(_args) -> int:
    _print("Available detectors (graders):")
    for name in sorted(DETECTORS):
        _print(f"  {name}")
    return 0


def cmd_validate(args) -> int:
    try:
        cfg = load_config(args.config)
    except Exception as exc:
        _print(f"INVALID: {exc}")
        return 1
    n_cases = sum(len(probes_mod.get_probe(p)(cfg.context)) for p in cfg.probes)
    planned = n_cases * len(cfg.strategies) * cfg.repeat
    _print("VALID")
    _print(f"  provider   : {cfg.target.get('provider')}")
    _print(f"  probes     : {', '.join(cfg.probes)}")
    _print(f"  strategies : {', '.join(cfg.strategies)}")
    _print(f"  repeat     : {cfg.repeat}")
    _print(f"  planned trials: {planned} ({n_cases} cases x {len(cfg.strategies)} strategies x {cfg.repeat} repeats)")
    return 0


def cmd_run(args) -> int:
    cfg = load_config(args.config)
    if args.repeat:
        cfg.repeat = args.repeat
    if args.provider:
        cfg.target["provider"] = args.provider

    provider = build_provider(cfg.target.get("provider", "mock"), **cfg.target)
    _print(f"Running Aegis against {provider.describe()} ...")

    trials = run_eval(cfg, provider=provider, progress=_print if args.verbose else None)
    card = score(trials)

    meta = {
        "target": provider.describe(),
        "repeat": cfg.repeat,
        "probes": cfg.probes,
        "strategies": cfg.strategies,
        "threshold": args.threshold,
    }
    payload = build_payload(trials, card, meta)

    report_dir = cfg.report.get("dir", "reports")
    formats = cfg.report.get("formats", ["html", "json", "csv"])
    os.makedirs(report_dir, exist_ok=True)
    base = os.path.join(report_dir, "aegis_report")
    if "json" in formats:
        write_json(payload, base + ".json")
    if "csv" in formats:
        write_csv(trials, base + ".csv")
    if "html" in formats:
        write_html(payload, base + ".html", threshold=args.threshold)

    _print("")
    _print("=== Scorecard ===")
    ov = card.overall
    _print(f"Overall ASR: {ov.asr:.0%}  ({ov.successes}/{ov.valid} valid trials, {ov.errors} errors)")
    _print("By category:")
    for name, g in sorted(card.by_probe.items()):
        _print(f"  {name:20s} ASR {g.asr:5.0%}  [{verdict(g.asr, args.threshold)}]")
    _print("By strategy:")
    for name, g in sorted(card.by_strategy.items()):
        _print(f"  {name:20s} ASR {g.asr:5.0%}")
    _print("")
    _print(f"Reports written to: {os.path.abspath(report_dir)}")
    return 0


def cmd_report(args) -> int:
    import json

    with open(args.result, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    out = args.output or os.path.splitext(args.result)[0] + ".html"
    write_html(payload, out, threshold=args.threshold)
    _print(f"HTML report written to: {os.path.abspath(out)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aegis",
        description="Aegis — local-first LLM security evaluation toolkit.",
    )
    sub = p.add_subparsers(dest="command")

    sub.add_parser("version", help="Show version").set_defaults(func=cmd_version)
    sub.add_parser("list-probes", help="List security categories").set_defaults(func=cmd_list_probes)
    sub.add_parser("list-strategies", help="List payload transforms").set_defaults(func=cmd_list_strategies)
    sub.add_parser("list-detectors", help="List graders").set_defaults(func=cmd_list_detectors)

    pv = sub.add_parser("validate", help="Validate a config file")
    pv.add_argument("-c", "--config", required=True)
    pv.set_defaults(func=cmd_validate)

    pr = sub.add_parser("run", help="Run an evaluation")
    pr.add_argument("-c", "--config", required=True)
    pr.add_argument("--repeat", type=int, default=None, help="Override repeat count")
    pr.add_argument("--provider", default=None, help="Override provider (e.g. mock, ollama)")
    pr.add_argument("--threshold", type=float, default=0.0, help="Max ASR to count as PASS")
    pr.add_argument("-v", "--verbose", action="store_true", help="Print per-trial progress")
    pr.set_defaults(func=cmd_run)

    prp = sub.add_parser("report", help="Regenerate HTML from a JSON result")
    prp.add_argument("result")
    prp.add_argument("-o", "--output", default=None)
    prp.add_argument("--threshold", type=float, default=0.0)
    prp.set_defaults(func=cmd_report)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except Exception as exc:
        _print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
