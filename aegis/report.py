"""Reporting — export results to JSON, CSV and a self-contained HTML page.

All three formats are written locally. The HTML has no external dependencies
(inline CSS) so it opens offline, matching the lab's local-evidence rule.
"""

from __future__ import annotations

import csv
import html
import io
import json
import os
from datetime import datetime, timezone
from typing import List

from .models import Trial
from .scoring import Scorecard, verdict


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def build_payload(trials: List[Trial], card: Scorecard, meta: dict) -> dict:
    """Assemble the canonical JSON-serialisable result object."""
    return {
        "tool": "aegis-redteam",
        "generated_at": _timestamp(),
        "meta": meta,
        "scorecard": card.as_dict(),
        "trials": [
            {
                "probe": t.probe,
                "intent": t.intent,
                "strategy": t.strategy,
                "repeat_index": t.repeat_index,
                "prompt": t.prompt,
                "response": t.response,
                "attack_success": t.grade.attack_success,
                "detector": t.grade.detector,
                "reason": t.grade.reason,
                "error": t.error,
            }
            for t in trials
        ],
    }


def write_json(payload: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def write_csv(trials: List[Trial], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["probe", "strategy", "repeat", "attack_success", "detector", "reason", "prompt", "response", "error"]
    )
    for t in trials:
        writer.writerow(
            [
                t.probe, t.strategy, t.repeat_index, t.grade.attack_success,
                t.grade.detector, t.grade.reason,
                t.prompt.replace("\n", " "), t.response.replace("\n", " "),
                t.error or "",
            ]
        )
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())


_CSS = """
body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;background:#0f172a;color:#e2e8f0}
.wrap{max-width:1000px;margin:0 auto;padding:32px 20px}
h1{font-size:24px;margin:0 0 4px} .sub{color:#94a3b8;margin:0 0 24px;font-size:13px}
.cards{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:24px}
.card{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px 18px;min-width:150px}
.card .k{font-size:12px;color:#94a3b8} .card .v{font-size:22px;font-weight:600;margin-top:4px}
table{width:100%;border-collapse:collapse;margin:8px 0 28px;font-size:13px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #334155;vertical-align:top}
th{color:#94a3b8;font-weight:600}
.pass{color:#4ade80;font-weight:600}.fail{color:#f87171;font-weight:600}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11px;background:#334155}
pre{white-space:pre-wrap;word-break:break-word;margin:0;font-size:12px;color:#cbd5e1}
h2{font-size:16px;margin:24px 0 8px;border-top:1px solid #334155;padding-top:18px}
"""


def _group_table(title: str, groups: dict, threshold: float) -> str:
    rows = []
    for name, g in groups.items():
        asr = g["attack_success_rate"]
        v = verdict(asr, threshold)
        cls = "pass" if v == "PASS" else "fail"
        rows.append(
            f"<tr><td>{html.escape(name)}</td><td>{g['valid']}</td>"
            f"<td>{g['attack_successes']}</td><td>{asr:.0%}</td>"
            f"<td class='{cls}'>{v}</td></tr>"
        )
    return (
        f"<h2>{html.escape(title)}</h2><table><tr><th>Name</th><th>Valid</th>"
        f"<th>Successes</th><th>ASR</th><th>Verdict</th></tr>{''.join(rows)}</table>"
    )


def write_html(payload: dict, path: str, threshold: float = 0.0) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    sc = payload["scorecard"]
    overall = sc["overall"]
    meta = payload["meta"]

    cards = "".join(
        f"<div class='card'><div class='k'>{html.escape(k)}</div><div class='v'>{html.escape(str(v))}</div></div>"
        for k, v in [
            ("Overall ASR", f"{overall['attack_success_rate']:.0%}"),
            ("Valid trials", overall["valid"]),
            ("Attack successes", overall["attack_successes"]),
            ("Errors", overall["errors"]),
            ("Target", meta.get("target", "?")),
        ]
    )

    trial_rows = []
    for t in payload["trials"]:
        cls = "fail" if t["attack_success"] else "pass"
        label = "ATTACK SUCCESS" if t["attack_success"] else "safe"
        trial_rows.append(
            f"<tr><td><span class='pill'>{html.escape(t['probe'])}</span></td>"
            f"<td>{html.escape(t['strategy'])}</td>"
            f"<td class='{cls}'>{label}</td>"
            f"<td><pre>{html.escape(t['prompt'][:400])}</pre></td>"
            f"<td><pre>{html.escape(t['response'][:400])}</pre></td>"
            f"<td>{html.escape(t['reason'])}</td></tr>"
        )

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aegis Red-Team Report</title><style>{_CSS}</style></head>
<body><div class="wrap">
<h1>Aegis Red-Team Report</h1>
<p class="sub">Generated {html.escape(payload['generated_at'])} &middot; target {html.escape(str(meta.get('target','?')))} &middot; repeat {html.escape(str(meta.get('repeat','?')))}</p>
<div class="cards">{cards}</div>
{_group_table("Results by security category", sc["by_probe"], threshold)}
{_group_table("Results by strategy", sc["by_strategy"], threshold)}
<h2>All trials</h2>
<table><tr><th>Category</th><th>Strategy</th><th>Result</th><th>Prompt</th><th>Response</th><th>Reason</th></tr>
{''.join(trial_rows)}</table>
</div></body></html>"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)
