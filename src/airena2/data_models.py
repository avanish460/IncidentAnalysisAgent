from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AlertRecord:
    id: str
    source: str
    severity: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class TicketRecord:
    id: str
    system: str
    category: str
    priority: str
    summary: str
    description: str
    created_at: datetime
    metadata: Dict[str, Any]


@dataclass
class IncidentEvent:
    id: str
    title: str
    severity: str
    classification: str
    alerts: List[AlertRecord]
    tickets: List[TicketRecord]
    summary: Optional[str] = None
    rca: Optional[str] = None
    recommendations: Optional[List[str]] = None
    metadata: Dict[str, Any] = None
