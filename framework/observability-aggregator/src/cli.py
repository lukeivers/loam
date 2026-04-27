"""`pos obs` CLI — thin wrapper over the structured Pydantic API.

Commands per brief D8:
  pos obs find-spans
  pos obs get-trace <trace_id>
  pos obs get-span <span_id>
  pos obs cost-by-prompt
  pos obs replay-session <session_id>
  pos obs replay-scope <scope_id>
  pos obs replay-objective <objective_id>
  pos obs audit-search
  pos obs why "<question>"     — invokes the NL path

Output is human-readable JSON (pretty-printed by default; --raw for
single-line). Every output cites span IDs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .api import EventFilter, QueryAPI, SpanFilter, TimeRange
from .config import AggregatorConfig
from .nl_path import NLPath
from .schema import RetentionClass
from .store import open_store


def _parse_time(s: str | None) -> datetime | None:
    if not s:
        return None
    if s.endswith("d"):
        return datetime.now(timezone.utc) - timedelta(days=int(s[:-1]))
    if s.endswith("h"):
        return datetime.now(timezone.utc) - timedelta(hours=int(s[:-1]))
    if s.endswith("m"):
        return datetime.now(timezone.utc) - timedelta(minutes=int(s[:-1]))
    return datetime.fromisoformat(s)


def _dump(obj: Any, raw: bool) -> str:
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump(mode="json")
    elif isinstance(obj, list) and obj and hasattr(obj[0], "model_dump"):
        obj = [o.model_dump(mode="json") for o in obj]
    elif isinstance(obj, dict):
        obj = {
            k: (v.model_dump(mode="json") if hasattr(v, "model_dump") else v)
            for k, v in obj.items()
        }
    if raw:
        return json.dumps(obj, default=str)
    return json.dumps(obj, default=str, indent=2)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("pos-obs", description="pOS observability aggregator CLI")
    p.add_argument("--db", help="Override DB path (default ~/.pos/observability.db)")
    p.add_argument("--substrate", choices=["duckdb", "sqlite"], help="Storage substrate")
    p.add_argument("--raw", action="store_true", help="Single-line JSON output")
    sub = p.add_subparsers(dest="command", required=True)

    p_find = sub.add_parser("find-spans", help="Search spans")
    p_find.add_argument("--component")
    p_find.add_argument("--name")
    p_find.add_argument("--status", choices=["OK", "ERROR", "UNSET"])
    p_find.add_argument("--scope-id")
    p_find.add_argument("--since", help="Time window start (e.g. '7d', '1h', or ISO)")
    p_find.add_argument("--retention-class", choices=["normal", "derived-only", "ephemeral"])
    p_find.add_argument("--limit", type=int, default=20)

    p_trace = sub.add_parser("get-trace", help="Fetch a full trace by trace_id")
    p_trace.add_argument("trace_id")

    p_span = sub.add_parser("get-span", help="Fetch a single span by span_id")
    p_span.add_argument("span_id")

    p_cost = sub.add_parser("cost-by-prompt", help="Aggregate cost by prompt name (v1.1 R12)")
    p_cost.add_argument("--since", help="Time window start (e.g. '7d', '1h', or ISO)")
    p_cost.add_argument("--component", action="append")

    p_rs = sub.add_parser("replay-session", help="Replay a session timeline")
    p_rs.add_argument("session_id")

    p_rsc = sub.add_parser("replay-scope", help="Replay a scope decision chain")
    p_rsc.add_argument("scope_id")

    p_ro = sub.add_parser("replay-objective", help="Replay an objective tree")
    p_ro.add_argument("objective_id")

    p_audit = sub.add_parser("audit-search", help="Search audit entries")
    p_audit.add_argument("--operation")
    p_audit.add_argument("--actor")
    p_audit.add_argument("--scope-id")
    p_audit.add_argument("--since")
    p_audit.add_argument("--limit", type=int, default=50)

    p_why = sub.add_parser("why", help="Natural-language query ('show me why')")
    p_why.add_argument("question")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = AggregatorConfig()
    if args.substrate:
        cfg.substrate = args.substrate
    if args.db:
        cfg.db_path = args.db
    store = open_store(cfg)
    try:
        api = QueryAPI(store)
        if args.command == "find-spans":
            f = SpanFilter(
                components=[args.component] if args.component else None,
                name_exact=args.name,
                status=args.status,
                scope_id=args.scope_id,
                time_range=(
                    TimeRange(start=_parse_time(args.since), end=datetime.now(timezone.utc))
                    if args.since else None
                ),
                retention_class=RetentionClass(args.retention_class) if args.retention_class else None,
            )
            print(_dump(api.find_spans(f, limit=args.limit), args.raw))
        elif args.command == "get-trace":
            print(_dump(api.get_trace(args.trace_id), args.raw))
        elif args.command == "get-span":
            print(_dump(api.get_span(args.span_id), args.raw))
        elif args.command == "cost-by-prompt":
            tw = (
                TimeRange(start=_parse_time(args.since), end=datetime.now(timezone.utc))
                if args.since else None
            )
            print(_dump(api.cost_by_prompt(time_range=tw, components=args.component), args.raw))
        elif args.command == "replay-session":
            print(_dump(api.replay_session(args.session_id), args.raw))
        elif args.command == "replay-scope":
            print(_dump(api.replay_scope(args.scope_id), args.raw))
        elif args.command == "replay-objective":
            print(_dump(api.replay_objective(args.objective_id), args.raw))
        elif args.command == "audit-search":
            tw = (
                TimeRange(start=_parse_time(args.since), end=datetime.now(timezone.utc))
                if args.since else None
            )
            rows = api.audit_search(
                operation=args.operation,
                actor=args.actor,
                scope_id=args.scope_id,
                time_range=tw,
                limit=args.limit,
            )
            print(_dump(rows, args.raw))
        elif args.command == "why":
            nl = NLPath(api)
            answer = nl.answer(args.question)
            print(_dump(answer, args.raw))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
