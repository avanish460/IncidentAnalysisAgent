"""Tests for ML-based incident classification."""

import pytest
from datetime import datetime
from airena2.data_models import AlertRecord, TicketRecord, IncidentEvent
from airena2.ml_classifier import MLIncidentClassifier


def test_ml_classifier_initialization() -> None:
    """Test ML classifier initializes properly."""
    classifier = MLIncidentClassifier()
    
    # Should initialize even if models don't exist yet
    assert classifier is not None
    # ml_enabled may be True or False depending on sklearn availability
    assert hasattr(classifier, 'ml_enabled')


def test_severity_classification() -> None:
    """Test severity classification."""
    classifier = MLIncidentClassifier()
    
    alerts = [
        AlertRecord(
            id="A1",
            source="server",
            severity="critical",
            message="Critical error detected",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
        AlertRecord(
            id="A2",
            source="server",
            severity="high",
            message="High load detected",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
    ]
    
    incident = IncidentEvent(
        id="inc-1",
        title="Test Incident",
        severity="P2",
        classification="service-impact",
        alerts=alerts,
        tickets=[],
        metadata={"alert_count": 2, "ticket_count": 0},
    )
    
    severity = classifier.classify_severity(incident)
    
    # Should return a valid priority
    assert severity in {"P1", "P2", "P3", "P4"}
    # Critical alerts should result in P1 or P2
    assert severity in {"P1", "P2"}


def test_impact_classification() -> None:
    """Test impact classification."""
    classifier = MLIncidentClassifier()
    
    alerts = [
        AlertRecord(
            id="A1",
            source="server",
            severity="critical",
            message="Service down",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
    ]
    
    incident = IncidentEvent(
        id="inc-1",
        title="Service Down",
        severity="P1",
        classification="informational",
        alerts=alerts,
        tickets=[],
        metadata={"alert_count": 1},
    )
    
    impact = classifier.classify_impact(incident)
    
    # Should return valid impact classification
    assert impact in {"service-impact", "informational"}
    # P1 severity should indicate service-impact
    assert impact == "service-impact"


def test_severity_fallback() -> None:
    """Test fallback severity classification when ML unavailable."""
    classifier = MLIncidentClassifier()
    # Force fallback
    classifier.severity_classifier = None
    
    alerts = [
        AlertRecord(
            id="A1",
            source="server",
            severity="critical",
            message="System down",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
    ]
    
    incident = IncidentEvent(
        id="inc-1",
        title="Critical Incident",
        severity="P3",
        classification="informational",
        alerts=alerts,
        tickets=[],
        metadata={"alert_count": 1},
    )
    
    severity = classifier.classify_severity(incident)
    
    # Fallback should still return valid severity
    assert severity in {"P1", "P2", "P3", "P4"}
    # Single critical alert should be P1
    assert severity == "P1"


def test_multiple_alerts_severity() -> None:
    """Test severity classification with multiple alerts."""
    classifier = MLIncidentClassifier()
    
    alerts = [
        AlertRecord(id=f"A{i}", source="server", severity="high",
                   message="Alert", timestamp=datetime.utcnow(), metadata={})
        for i in range(5)
    ]
    
    incident = IncidentEvent(
        id="inc-1",
        title="Multi-Alert Incident",
        severity="P3",
        classification="informational",
        alerts=alerts,
        tickets=[],
        metadata={"alert_count": 5},
    )
    
    severity = classifier.classify_severity(incident)
    
    # Multiple alerts should increase severity
    assert severity in {"P1", "P2"}


def test_impact_with_tickets() -> None:
    """Test impact classification with multiple tickets."""
    classifier = MLIncidentClassifier()
    
    alerts = [
        AlertRecord(id="A1", source="server", severity="high",
                   message="Alert", timestamp=datetime.utcnow(), metadata={}),
    ]
    
    tickets = [
        TicketRecord(id="T1", system="ServiceNow", category="incident",
                    priority="high", summary="Issue", description="Desc",
                    created_at=datetime.utcnow(), metadata={}),
        TicketRecord(id="T2", system="Jira", category="incident",
                    priority="high", summary="Issue 2", description="Desc 2",
                    created_at=datetime.utcnow(), metadata={}),
    ]
    
    incident = IncidentEvent(
        id="inc-1",
        title="Multi-Ticket Incident",
        severity="P2",
        classification="informational",
        alerts=alerts,
        tickets=tickets,
        metadata={"alert_count": 1, "ticket_count": 2},
    )
    
    impact = classifier.classify_impact(incident)
    
    # Multiple tickets + P2 severity should be service-impact
    assert impact == "service-impact"
