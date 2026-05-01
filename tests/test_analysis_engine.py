"""Tests for enhanced analysis engine."""

from datetime import datetime
from airena2.data_models import AlertRecord, TicketRecord, IncidentEvent
from airena2.analysis import AnalysisEngine


def test_analysis_engine_initialization() -> None:
    """Test analysis engine initializes with all components."""
    engine = AnalysisEngine()
    
    assert engine is not None
    # Check that components are attempted to be loaded
    assert hasattr(engine, 'llm')
    assert hasattr(engine, 'classifier')
    assert hasattr(engine, 'correlator')
    assert hasattr(engine, 'summarizer')
    assert hasattr(engine, 'feedback')


def test_summarize_incident() -> None:
    """Test incident summarization."""
    engine = AnalysisEngine()
    
    alerts = [
        AlertRecord(
            id="A1",
            source="app-server",
            severity="high",
            message="CPU usage exceeded 95%",
            timestamp=datetime.utcnow(),
            metadata={"service": "payments"},
        ),
    ]
    
    incident = IncidentEvent(
        id="inc-1",
        title="Payment Service Degradation",
        severity="P2",
        classification="service-impact",
        alerts=alerts,
        tickets=[],
        metadata={"alert_count": 1, "ticket_count": 0},
    )
    
    summary = engine.summarize_incident(incident)
    
    assert summary is not None
    assert len(summary) > 0
    # Should contain incident info
    assert "P2" in summary or "incident" in summary.lower()


def test_generate_rca() -> None:
    """Test RCA generation."""
    engine = AnalysisEngine()
    
    alerts = [
        AlertRecord(
            id="A1",
            source="server",
            severity="high",
            message="Database connection failures",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
        AlertRecord(
            id="A2",
            source="server",
            severity="high",
            message="API timeout",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
    ]
    
    incident = IncidentEvent(
        id="inc-1",
        title="Multi-System Failure",
        severity="P1",
        classification="service-impact",
        alerts=alerts,
        tickets=[],
        metadata={"alert_count": 2},
    )
    
    rca = engine.generate_rca(incident)
    
    assert rca is not None
    assert len(rca) > 0


def test_recommend_actions() -> None:
    """Test action recommendations."""
    engine = AnalysisEngine()
    
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
        title="Critical Service Down",
        severity="P1",
        classification="service-impact",
        alerts=alerts,
        tickets=[],
        metadata={"alert_count": 1},
    )
    
    recommendations = engine.recommend_actions(incident)
    
    assert recommendations is not None
    assert len(recommendations) > 0
    assert all(isinstance(r, str) for r in recommendations)
    # P1 severity should include urgent actions
    assert any("urgent" in r.lower() or "critical" in r.lower() for r in recommendations)


def test_refine_incident_classification() -> None:
    """Test incident classification refinement."""
    engine = AnalysisEngine()
    
    alerts = [
        AlertRecord(
            id="A1",
            source="server",
            severity="critical",
            message="Critical error",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
    ]
    
    incident = IncidentEvent(
        id="inc-1",
        title="Critical Incident",
        severity="P4",  # Intentionally low
        classification="informational",
        alerts=alerts,
        tickets=[],
        metadata={"alert_count": 1},
    )
    
    # Should not raise error
    engine.refine_incident_classification(incident)
    # Original severity should be unchanged
    assert incident.severity == "P4"


def test_record_feedback() -> None:
    """Test recording feedback."""
    engine = AnalysisEngine()
    
    alerts = [
        AlertRecord(
            id="A1",
            source="server",
            severity="high",
            message="Alert",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
    ]
    
    incident = IncidentEvent(
        id="inc-1",
        title="Test Incident",
        severity="P1",
        classification="service-impact",
        alerts=alerts,
        tickets=[],
        metadata={"alert_count": 1},
    )
    
    # Should not raise error
    engine.record_feedback(
        incident=incident,
        actual_severity="P2",
        user_comments="Too severe",
    )


def test_multiple_alerts_summarization() -> None:
    """Test summarization with multiple alerts and tickets."""
    engine = AnalysisEngine()
    
    alerts = [
        AlertRecord(
            id=f"A{i}",
            source=f"server-{i}",
            severity="high",
            message="System error detected",
            timestamp=datetime.utcnow(),
            metadata={},
        )
        for i in range(3)
    ]
    
    tickets = [
        TicketRecord(
            id=f"T{i}",
            system="ServiceNow",
            category="incident",
            priority="high",
            summary=f"Issue {i}",
            description=f"Description {i}",
            created_at=datetime.utcnow(),
            metadata={},
        )
        for i in range(2)
    ]
    
    incident = IncidentEvent(
        id="inc-1",
        title="Multi-Alert Incident",
        severity="P1",
        classification="service-impact",
        alerts=alerts,
        tickets=tickets,
        metadata={"alert_count": 3, "ticket_count": 2},
    )
    
    summary = engine.summarize_incident(incident)
    rca = engine.generate_rca(incident)
    recommendations = engine.recommend_actions(incident)
    
    assert summary is not None and len(summary) > 0
    assert rca is not None and len(rca) > 0
    assert recommendations is not None and len(recommendations) > 0
