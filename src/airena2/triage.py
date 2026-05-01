from __future__ import annotations

from typing import List, Optional

from .data_models import AlertRecord, IncidentEvent, TicketRecord

try:
    from .correlation import SemanticCorrelationEngine
except ImportError:
    SemanticCorrelationEngine = None


class TriageEngine:
    """Advanced triage and semantic alert correlation."""

    def __init__(self):
        """Initialize triage engine with semantic correlation."""
        self.correlator: Optional[SemanticCorrelationEngine] = None
        if SemanticCorrelationEngine is not None:
            try:
                self.correlator = SemanticCorrelationEngine()
            except Exception as e:
                print(f"[WARN] Failed to initialize semantic correlator: {e}")

    def classify_alert(self, alert: AlertRecord) -> str:
        """Classify alert severity to priority.
        
        Args:
            alert: AlertRecord to classify
            
        Returns:
            Priority string (P1-P4)
        """
        severity_map = {"critical": "P1", "high": "P2", "medium": "P3", "low": "P4"}
        return severity_map.get(alert.severity.lower(), "P3")

    def correlate_alerts(self, alerts: List[AlertRecord], similarity_threshold: float = 0.6) -> List[List[AlertRecord]]:
        """Group alerts using semantic similarity.
        
        Args:
            alerts: List of alerts to correlate
            similarity_threshold: Minimum similarity to group alerts
            
        Returns:
            List of alert groups
        """
        if not alerts:
            return []
        
        # Try semantic correlation first
        if self.correlator is not None:
            try:
                return self.correlator.correlate_alerts(alerts, similarity_threshold=similarity_threshold)
            except Exception as e:
                print(f"[WARN] Semantic correlation failed, using fallback: {e}")
        
        # Fallback to simple source-based grouping
        return self._correlate_alerts_fallback(alerts)

    def _correlate_alerts_fallback(self, alerts: List[AlertRecord]) -> List[List[AlertRecord]]:
        """Fallback alert correlation by source."""
        groups: List[List[AlertRecord]] = []
        seen = set()
        for alert in alerts:
            if alert.source not in seen:
                groups.append([alert])
                seen.add(alert.source)
        return groups

    def build_incident(self, alerts: List[AlertRecord], tickets: List[TicketRecord]) -> IncidentEvent:
        """Build incident event from alerts and tickets.
        
        Args:
            alerts: List of alerts
            tickets: List of tickets
            
        Returns:
            IncidentEvent
        """
        incident_id = f"incident-{alerts[0].id if alerts else 'unknown'}"
        classification = self.classify_alert(alerts[0]) if alerts else "P3"
        
        # Use semantic correlation for grouping
        correlated_groups = self.correlate_alerts(alerts) if alerts else []
        primary_group = correlated_groups[0] if correlated_groups else []
        
        return IncidentEvent(
            id=incident_id,
            title=f"Incident from {alerts[0].source if alerts else 'unknown source'}",
            severity=classification,
            classification="service-impact" if classification in {"P1", "P2"} else "informational",
            alerts=alerts,
            tickets=tickets,
            metadata={
                "alert_count": len(alerts),
                "ticket_count": len(tickets),
                "correlation_groups": len(correlated_groups),
                "primary_group_size": len(primary_group),
            },
        )
