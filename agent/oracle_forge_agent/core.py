from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from .toolbox_client import ToolboxClient, _safe_json
from .types import AgentResponse, ToolCallTrace


def run_agent(question: str) -> AgentResponse:
    """
    Minimal Sprint-1 agent:
    - Connects to MCP Toolbox
    - Performs simple schema discovery for SQLite/Postgres
    - Returns a trace + a safe, verifiable answer (even if partial)
    """

    trace: List[ToolCallTrace] = []
    client = ToolboxClient()

    ok, status, tools = client.list_tools()
    trace.append(
        ToolCallTrace(
            tool_name="GET /v1/tools",
            parameters={},
            ok=ok,
            status_code=status,
            result_summary=_summarize_tools(tools) if ok else None,
            result=tools if ok else None,
            error=None if ok else _summarize_error(tools),
        )
    )

    if not ok:
        return AgentResponse(
            answer="Toolbox is not reachable or returned an error. Start the toolbox with `./toolbox --config mcp/tools.yaml` and retry.",
            query_trace=trace,
            confidence="low",
            notes=f"TOOLBOX_URL={client.base_url}",
        )

    # Naive “first useful action”: discover what tables exist in SQLite and Postgres.
    # If Postgres is not loaded yet, it may error; we keep the failure in the trace.
    _try_invoke(client, trace, "sqlite-list-tables", {})
    _try_invoke(client, trace, "list-tables", {})

    # Basic response: echo what we found; this is verifiable and provides grounding.
    sqlite_tables = _extract_table_names_from_trace(trace, "sqlite-list-tables")
    pg_tables = _extract_table_names_from_trace(trace, "list-tables")

    answer_lines: List[str] = []
    answer_lines.append("Connected to MCP Toolbox and performed initial schema discovery.")

    if sqlite_tables is not None:
        answer_lines.append(f"SQLite tables ({len(sqlite_tables)}): {', '.join(sqlite_tables[:30])}{' ...' if len(sqlite_tables) > 30 else ''}")
    else:
        answer_lines.append("SQLite table discovery failed (see query_trace).")

    if pg_tables is not None:
        answer_lines.append(f"PostgreSQL tables ({len(pg_tables)}): {', '.join(pg_tables[:30])}{' ...' if len(pg_tables) > 30 else ''}")
    else:
        answer_lines.append("PostgreSQL table discovery failed (see query_trace).")

    answer_lines.append("")
    answer_lines.append(f"Question received: {question}")
    answer_lines.append("Next step: implement question→query planning once target dataset tables are confirmed.")

    confidence = "medium" if sqlite_tables else "low"
    return AgentResponse(answer="\n".join(answer_lines), query_trace=trace, confidence=confidence)


def _try_invoke(client: ToolboxClient, trace: List[ToolCallTrace], tool_name: str, parameters: Dict[str, Any]) -> None:
    try:
        r = client.invoke(tool_name, parameters=parameters)
        payload = _safe_json(r)
        trace.append(
            ToolCallTrace(
                tool_name=tool_name,
                parameters=parameters,
                ok=r.ok,
                status_code=r.status_code,
                result=payload if r.ok else None,
                error=None if r.ok else _summarize_error(payload),
                result_summary=_summarize_result(payload) if r.ok else None,
            )
        )
    except Exception as e:  # noqa: BLE001
        trace.append(
            ToolCallTrace(
                tool_name=tool_name,
                parameters=parameters,
                ok=False,
                status_code=None,
                error=str(e),
            )
        )


def _summarize_tools(payload: Any) -> str:
    # Toolbox often returns {"tools":[...]} but we keep it flexible.
    if isinstance(payload, dict) and "tools" in payload and isinstance(payload["tools"], list):
        names = []
        for t in payload["tools"]:
            if isinstance(t, dict) and "name" in t:
                names.append(str(t["name"]))
        return f"{len(names)} tools: {', '.join(names[:20])}{' ...' if len(names) > 20 else ''}"
    return "Tools listed"


def _summarize_result(payload: Any) -> str:
    if payload is None:
        return "No result"
    if isinstance(payload, list):
        return f"List[{len(payload)}]"
    if isinstance(payload, dict):
        # Common shapes: {"rows":[...]} / {"result":...}
        if "rows" in payload and isinstance(payload["rows"], list):
            return f"rows={len(payload['rows'])}"
        return f"keys={sorted(list(payload.keys()))[:10]}"
    return f"type={type(payload).__name__}"


def _summarize_error(payload: Any) -> str:
    if payload is None:
        return "Unknown error"
    if isinstance(payload, dict):
        for k in ("error", "message", "detail"):
            if k in payload and isinstance(payload[k], str):
                return payload[k]
    return str(payload)[:500]


def _extract_table_names_from_trace(trace: List[ToolCallTrace], tool_name: str) -> Optional[List[str]]:
    for t in trace:
        if t.tool_name != tool_name or not t.ok:
            continue
        payload = t.result
        # common: [{"name":"table"}] or [["table"], ...] or {"rows":[{"table_name":"..."}]}
        names: List[str] = []
        if isinstance(payload, list):
            for row in payload:
                if isinstance(row, dict):
                    for k in ("table_name", "name"):
                        if k in row:
                            names.append(str(row[k]))
                            break
                elif isinstance(row, (list, tuple)) and row:
                    names.append(str(row[0]))
        elif isinstance(payload, dict) and "rows" in payload and isinstance(payload["rows"], list):
            for row in payload["rows"]:
                if isinstance(row, dict):
                    for k in ("table_name", "name"):
                        if k in row:
                            names.append(str(row[k]))
                            break
        return names if names else []
    return None

