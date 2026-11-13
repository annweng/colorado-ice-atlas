"""Shared HTTP helpers. Do not log secrets."""

from __future__ import annotations

import time
from typing import Any

import httpx

USER_AGENT = "ColoradoIceAtlas/0.1 (open environmental atlas; github actions)"


def json_get(url: str, params: dict[str, Any] | None = None, timeout: float = 60.0, retries: int = 4) -> Any:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed after {retries} attempts: {last_exc}") from last_exc


def json_post(url: str, payload: dict[str, Any], timeout: float = 60.0, retries: int = 3) -> Any:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"}) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"POST {url} failed after {retries} attempts: {last_exc}") from last_exc
