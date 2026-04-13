from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ToolCallTrace(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    ok: bool
    status_code: Optional[int] = None
    error: Optional[str] = None
    result_summary: Optional[str] = None
    result: Optional[Any] = None


class AgentResponse(BaseModel):
    answer: str
    query_trace: List[ToolCallTrace]
    confidence: Literal["high", "medium", "low"]
    notes: Optional[str] = None

