"""Transcripts of a run for the researcher (SPEC §17: `sambhasha transcript`).

Unlike a seat's view, a transcript shows everything: every event with its time, seat, type,
who could see it and where its text came from, and each model call with its tokens and cost.
It holds the run's answers, so it stays private like the case bundles.
"""

import html
from collections.abc import Sequence
from decimal import Decimal

from sambhasha.domain.events import Event
from sambhasha.domain.orders import Order
from sambhasha.domain.runs import Run
from sambhasha.engine.chart import render
from sambhasha.engine.clock import MINUTES_PER_DAY


def _when(minutes: int) -> str:
    day, rest = divmod(minutes, MINUTES_PER_DAY)
    return f"day {day} {rest // 60:02d}:{rest % 60:02d}"


def _text(event: Event) -> str:
    if event.type == "llm_call":
        cost = "?" if event.cost_usd is None else f"USD {event.cost_usd}"
        payload = event.payload.model_dump()
        cached = " (cached)" if payload.get("cached") else ""
        return (
            f"model {event.model}, prompt v{event.prompt_version}, "
            f"{event.tokens_in} in / {event.tokens_out} out, {cost}{cached}"
        )
    return render(event.payload)


def _audience(event: Event) -> str:
    return ", ".join(event.visibility) or "no seat"


def _summary(run: Run, events: Sequence[Event], orders: Sequence[Order]) -> list[str]:
    spent = sum((e.cost_usd or Decimal(0) for e in events if e.type == "llm_call"), Decimal(0))
    tests = sum((o.cost_inr for o in orders if o.status != "cancelled"), Decimal(0))
    final_hash = events[-1].hash if events else None
    return [
        f"Run {run.id} on {run.bundle_id} ({run.status})",
        f"Engine {run.engine_version}; config {run.config_hash[:12]}; events {len(events)}; "
        f"final hash {(final_hash or '-')[:16]}",
        f"Tests ordered: {len(orders)}, INR {tests}; model calls: USD {spent}",
    ]


def render_text(run: Run, events: Sequence[Event], orders: Sequence[Order]) -> str:
    lines = [*_summary(run, events, orders), ""]
    for event in events:
        text = _text(event).replace("\n", "\n    ")
        lines.append(
            f"[{event.event_id} · {_when(event.sim_minutes)} · {event.seat} · {event.type}"
            f" · {event.source} · to {_audience(event)}] {text}"
        )
    return "\n".join(lines) + "\n"


def render_html(run: Run, events: Sequence[Event], orders: Sequence[Order]) -> str:
    rows = "\n".join(
        "<tr class='{kind}'><td>{id}</td><td>{when}</td><td>{seat}</td><td>{kind}</td>"
        "<td>{source}</td><td>{audience}</td><td>{text}</td></tr>".format(
            id=html.escape(e.event_id),
            when=html.escape(_when(e.sim_minutes)),
            seat=html.escape(e.seat),
            kind=html.escape(e.type),
            source=html.escape(e.source),
            audience=html.escape(_audience(e)),
            text=html.escape(_text(e)).replace("\n", "<br>"),
        )
        for e in events
    )
    summary = "".join(f"<p>{html.escape(line)}</p>" for line in _summary(run, events, orders))
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<title>Sambhasha run {html.escape(str(run.id))}</title>
<style>
body {{ font: 14px/1.45 system-ui, sans-serif; margin: 24px; color: #1d1d1f; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #ddd; padding: 6px 8px; text-align: left; vertical-align: top; }}
th {{ background: #f3f3f3; position: sticky; top: 0; }}
tr.llm_call td {{ color: #777; font-size: 12px; }}
tr.refusal td {{ background: #fff5f5; }}
tr.commit td, tr.challenge td {{ background: #f5f8ff; }}
</style>
</head>
<body>
<h1>Sambhasha transcript</h1>
{summary}
<p><strong>Private:</strong> this transcript shows the case's answers. Do not publish it.</p>
<table>
<thead><tr><th>Event</th><th>Time</th><th>Seat</th><th>Type</th><th>Source</th>
<th>Seen by</th><th>Text</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>
"""
