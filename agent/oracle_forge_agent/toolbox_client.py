from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Tuple

import requests


class ToolboxClient:
    """
    Minimal HTTP client for Google MCP Toolbox.

    The toolbox API has varied across versions; this client tries a couple of
    common invoke endpoints so we can run on whichever is available.
    """

    def __init__(self, base_url: Optional[str] = None, timeout_s: int = 30):
        self.base_url = (base_url or os.environ.get("TOOLBOX_URL") or "http://localhost:5000").rstrip("/")
        self.timeout_s = timeout_s

    def list_tools(self) -> Tuple[bool, int, Any]:
        url = f"{self.base_url}/v1/tools"
        r = requests.get(url, timeout=self.timeout_s)
        return r.ok, r.status_code, _safe_json(r)

    def invoke(self, tool_name: str, parameters: Optional[Dict[str, Any]] = None) -> requests.Response:
        params = parameters or {}

        # Attempt A: REST-style tool invocation
        url_a = f"{self.base_url}/v1/tools/{tool_name}:invoke"
        payload_a = {"parameters": params}

        # Attempt B: generic invoke endpoint (some builds)
        url_b = f"{self.base_url}/v1/tools:invoke"
        payload_b = {"tool": tool_name, "parameters": params}

        last_exc: Optional[Exception] = None

        for url, payload in ((url_a, payload_a), (url_b, payload_b)):
            try:
                r = requests.post(url, json=payload, timeout=self.timeout_s)
                if r.status_code != 404:
                    return r
            except Exception as e:  # noqa: BLE001
                last_exc = e

        if last_exc:
            raise last_exc

        # If both endpoints 404, return the last response by re-requesting url_a
        return requests.post(url_a, json=payload_a, timeout=self.timeout_s)


def _safe_json(r: requests.Response) -> Any:
    try:
        return r.json()
    except Exception:  # noqa: BLE001
        text = r.text
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:  # noqa: BLE001
            return {"raw": text}

