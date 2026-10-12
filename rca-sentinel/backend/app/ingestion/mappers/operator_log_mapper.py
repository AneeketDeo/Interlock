"""Operator shift log mapper.

Maps operator spreadsheet entries and free-text shift notes into OperatorLog dicts.
Extracts keywords and tags for graph search and evidence correlation.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from app.ingestion.entity_resolution import EntityResolver


class OperatorLogMapper:
    """Transforms operator shift notes into OperatorLog entities."""

    KEYWORD_PATTERNS: ClassVar[dict[str, re.Pattern[str]]] = {
        "spindle": re.compile(r"\bspindle\b", re.IGNORECASE),
        "vibration": re.compile(r"\b(vibrat|chatter|hum)\w*\b", re.IGNORECASE),
        "temperature": re.compile(r"\b(warm|hot|overheat|temp)\w*\b", re.IGNORECASE),
        "bearing": re.compile(r"\bbearing\b", re.IGNORECASE),
        "feed_rate": re.compile(r"\bfeed\s*rate\b", re.IGNORECASE),
        "scrap": re.compile(r"\bscrap\b", re.IGNORECASE),
        "micro_cracks": re.compile(r"\b(crack|fracture)\w*\b", re.IGNORECASE),
    }

    def __init__(self, resolver: EntityResolver | None = None) -> None:
        self.resolver = resolver or EntityResolver()

    def map_log(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Convert a raw shift log entry into an OperatorLog dict."""
        raw_machine = str(raw.get("machine_id") or raw.get("station", ""))
        machine_id = self.resolver.resolve_machine_id(raw_machine)
        text = str(raw.get("text") or raw.get("notes") or "")

        tags = list(raw.get("tags") or [])
        if not tags:
            for tag_name, pattern in self.KEYWORD_PATTERNS.items():
                if pattern.search(text):
                    tags.append(tag_name)

        return {
            "id": str(raw.get("id") or f"log-{hash(text)}"),
            "machine_id": machine_id,
            "operator_id": str(raw.get("operator_id") or "op-anonymous"),
            "operator_name": str(raw.get("operator_name") or "Operator"),
            "shift": int(raw.get("shift", 1)),
            "timestamp": raw.get("timestamp") or "",
            "text": text,
            "tags": tags,
        }
