from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .data_models import IncidentEvent
from .db_service import DatabaseService, IncidentRepository


class IncidentStore:
    """Storage for analyzed incidents with optional persistence."""

    def __init__(self, use_database: bool = True, database_url: Optional[str] = None) -> None:
        """Initialize incident store.
        
        Args:
            use_database: Whether to use database persistence
            database_url: Optional database URL. If None, uses default SQLite.
        """
        self._incidents: Dict[str, Dict[str, Any]] = {}
        self.use_database = use_database
        self.db_service: Optional[DatabaseService] = None
        self.incident_repo: Optional[IncidentRepository] = None
        
        if use_database:
            self.db_service = DatabaseService(database_url)
            self.db_service.initialize_db()
            self.incident_repo = IncidentRepository(self.db_service)

    def add_incident(
        self,
        incident: IncidentEvent,
        processed_at: Optional[str] = None,
        impacted_services: Optional[List[str]] = None,
    ) -> None:
        processed_at = processed_at or datetime.utcnow().isoformat()
        record = {
            "incident_id": incident.id,
            "title": incident.title,
            "severity": incident.severity,
            "classification": incident.classification,
            "summary": incident.summary,
            "rca": incident.rca,
            "recommendations": incident.recommendations or [],
            "alert_count": len(incident.alerts),
            "ticket_count": len(incident.tickets),
            "processed_at": processed_at,
            "metadata": incident.metadata or {},
            "alerts": [self._alert_to_dict(alert) for alert in incident.alerts],
            "tickets": [self._ticket_to_dict(ticket) for ticket in incident.tickets],
            "impacted_services": impacted_services or [],
        }
        
        self._incidents[incident.id] = record
        
        # Also persist to database if enabled
        if self.use_database and self.incident_repo:
            self.incident_repo.create_incident(
                incident_id=incident.id,
                title=incident.title,
                severity=incident.severity,
                classification=incident.classification,
                summary=incident.summary,
                rca=incident.rca,
                recommendations=incident.recommendations,
                impacted_services=impacted_services,
                alert_count=len(incident.alerts),
                ticket_count=len(incident.tickets),
                alerts=[self._alert_to_dict(alert) for alert in incident.alerts],
                tickets=[self._ticket_to_dict(ticket) for ticket in incident.tickets],
                metadata=incident.metadata,
                processed_at=processed_at,
            )

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        # Check database first if enabled
        if self.use_database and self.incident_repo:
            db_result = self.incident_repo.get_incident(incident_id)
            if db_result:
                return db_result
        
        # Fallback to in-memory
        return self._incidents.get(incident_id)

    def list_incidents(
        self,
        severity: Optional[str] = None,
        classification: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        # Use database if enabled
        if self.use_database and self.incident_repo:
            return self.incident_repo.list_incidents(
                severity=severity,
                classification=classification,
            )
        
        # Fallback to in-memory
        incidents = list(self._incidents.values())

        if severity:
            incidents = [i for i in incidents if i["severity"] == severity]
        if classification:
            incidents = [i for i in incidents if i["classification"] == classification]

        return incidents

    def clear(self) -> None:
        self._incidents.clear()
        # Note: Database is not cleared to preserve data across sessions
        # Use database cleanup tools if needed

    def count(self) -> int:
        if self.use_database and self.incident_repo:
            return self.incident_repo.count_incidents()
        return len(self._incidents)

    @staticmethod
    def _alert_to_dict(alert: Any) -> Dict[str, Any]:
        return {
            "id": alert.id,
            "source": alert.source,
            "severity": alert.severity,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "metadata": alert.metadata,
        }

    @staticmethod
    def _ticket_to_dict(ticket: Any) -> Dict[str, Any]:
        return {
            "id": ticket.id,
            "system": ticket.system,
            "category": ticket.category,
            "priority": ticket.priority,
            "summary": ticket.summary,
            "description": ticket.description,
            "created_at": ticket.created_at.isoformat(),
            "metadata": ticket.metadata,
        }
