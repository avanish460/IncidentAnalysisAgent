"""Tests for persistence layer."""

import os
import tempfile
from datetime import datetime

from airena2.data_models import IncidentEvent, AlertRecord, TicketRecord
from airena2.db_service import DatabaseService, IncidentRepository, FeedbackRepository
from airena2.incident_manager import IncidentStore


def test_database_service_initialization():
    """Test database service initialization."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_url = f"sqlite:///{os.path.join(tmp_dir, 'test.db')}"
        db_service = DatabaseService(db_url)
        db_service.initialize_db()
        
        # Should not raise any errors
        session = db_service.get_session()
        assert session is not None
        session.close()


def test_incident_repository_create_and_retrieve():
    """Test creating and retrieving incidents."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_url = f"sqlite:///{os.path.join(tmp_dir, 'test.db')}"
        db_service = DatabaseService(db_url)
        db_service.initialize_db()
        
        repo = IncidentRepository(db_service)
        
        # Create an incident
        result = repo.create_incident(
            incident_id="test-incident-1",
            title="Test Incident",
            severity="P1",
            classification="incident",
            summary="Test summary",
            rca="Test RCA",
            recommendations=["Rec 1", "Rec 2"],
            alert_count=5,
            ticket_count=2,
        )
        
        assert result["incident_id"] == "test-incident-1"
        assert result["title"] == "Test Incident"
        assert result["severity"] == "P1"
        
        # Retrieve the incident
        retrieved = repo.get_incident("test-incident-1")
        assert retrieved is not None
        assert retrieved["incident_id"] == "test-incident-1"
        assert retrieved["alert_count"] == 5


def test_incident_repository_list_with_filters():
    """Test listing incidents with filters."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_url = f"sqlite:///{os.path.join(tmp_dir, 'test.db')}"
        db_service = DatabaseService(db_url)
        db_service.initialize_db()
        
        repo = IncidentRepository(db_service)
        
        # Create multiple incidents
        repo.create_incident("inc-1", "Critical Issue", "P1", "incident")
        repo.create_incident("inc-2", "Medium Issue", "P2", "incident")
        repo.create_incident("inc-3", "Info Event", "P3", "informational")
        
        # List by severity
        p1_incidents = repo.list_incidents(severity="P1")
        assert len(p1_incidents) == 1
        assert p1_incidents[0]["incident_id"] == "inc-1"
        
        # List by classification
        incident_records = repo.list_incidents(classification="incident")
        assert len(incident_records) == 2


def test_incident_store_with_database():
    """Test IncidentStore with database persistence."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_url = f"sqlite:///{os.path.join(tmp_dir, 'test.db')}"
        
        # Create store with database
        store = IncidentStore(use_database=True, database_url=db_url)
        
        # Create an incident
        event = IncidentEvent(
            id="stored-incident-1",
            title="Stored Incident",
            severity="P1",
            classification="incident",
            summary="Test summary",
            rca="Test RCA",
            recommendations=["Rec 1"],
            alerts=[
                AlertRecord(
                    id="A1",
                    source="test",
                    severity="critical",
                    message="Test alert",
                    timestamp=datetime.utcnow(),
                    metadata={},
                )
            ],
            tickets=[
                TicketRecord(
                    id="T1",
                    system="Test",
                    category="incident",
                    priority="high",
                    summary="Test ticket",
                    description="Test description",
                    created_at=datetime.utcnow(),
                    metadata={},
                )
            ],
            metadata={},
        )
        
        store.add_incident(event, impacted_services=["service-1"])
        
        # Retrieve the incident
        retrieved = store.get_incident("stored-incident-1")
        assert retrieved is not None
        assert retrieved["incident_id"] == "stored-incident-1"
        assert retrieved["alert_count"] == 1
        assert retrieved["ticket_count"] == 1
        assert "service-1" in retrieved["impacted_services"]


def test_incident_store_count():
    """Test incident store count."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_url = f"sqlite:///{os.path.join(tmp_dir, 'test.db')}"
        
        store = IncidentStore(use_database=True, database_url=db_url)
        
        initial_count = store.count()
        
        # Add incidents
        for i in range(3):
            event = IncidentEvent(
                id=f"incident-{i}",
                title=f"Incident {i}",
                severity="P2",
                classification="incident",
                summary="Test",
                rca="Test",
                recommendations=[],
                alerts=[],
                tickets=[],
                metadata={},
            )
            store.add_incident(event)
        
        assert store.count() == initial_count + 3


def test_feedback_repository():
    """Test feedback repository."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_url = f"sqlite:///{os.path.join(tmp_dir, 'test.db')}"
        db_service = DatabaseService(db_url)
        db_service.initialize_db()
        
        repo = FeedbackRepository(db_service)
        
        # Create feedback
        feedback = repo.create_feedback(
            incident_id="test-incident",
            predicted_severity="P1",
            predicted_impact="incident",
            actual_severity="P2",
            is_accurate=False,
            correction_made=True,
        )
        
        assert feedback["incident_id"] == "test-incident"
        assert feedback["predicted_severity"] == "P1"
        assert feedback["actual_severity"] == "P2"
        
        # Get metrics
        metrics = repo.get_metrics()
        assert metrics["total_feedback"] >= 1
        assert metrics["inaccurate_predictions"] >= 1
