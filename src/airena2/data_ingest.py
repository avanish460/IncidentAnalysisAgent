from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List

from .data_models import AlertRecord, TicketRecord


class DataIngestor:
    """Load and normalize incident source records."""

    def load_alerts(self, data: Iterable[Dict[str, Any]]) -> List[AlertRecord]:
        records: List[AlertRecord] = []
        for item in data:
            records.append(
                AlertRecord(
                    id=str(item.get("id", "")),
                    source=item.get("source", "unknown"),
                    severity=item.get("severity", "medium"),
                    message=item.get("message", ""),
                    timestamp=self._parse_timestamp(item.get("timestamp")),
                    metadata=item.get("metadata", {}),
                )
            )
        return records

    def load_tickets(self, data: Iterable[Dict[str, Any]]) -> List[TicketRecord]:
        records: List[TicketRecord] = []
        for item in data:
            records.append(
                TicketRecord(
                    id=str(item.get("id", "")),
                    system=item.get("system", "unknown"),
                    category=item.get("category", "incident"),
                    priority=item.get("priority", "medium"),
                    summary=item.get("summary", ""),
                    description=item.get("description", ""),
                    created_at=self._parse_timestamp(item.get("created_at")),
                    metadata=item.get("metadata", {}),
                )
            )
        return records

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.utcnow()
