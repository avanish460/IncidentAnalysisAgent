"""Tests for feedback capture and learning system."""

import pytest
import os
import shutil
from datetime import datetime
from airena2.feedback import FeedbackCapture


@pytest.fixture
def feedback_system():
    """Create a feedback system for testing."""
    feedback = FeedbackCapture()
    # Override directory for testing
    feedback.FEEDBACK_DIR = ".test_feedback"
    feedback.FEEDBACK_FILE = os.path.join(feedback.FEEDBACK_DIR, "feedback.jsonl")
    feedback.METRICS_FILE = os.path.join(feedback.FEEDBACK_DIR, "metrics.json")
    feedback._ensure_feedback_dir()
    
    yield feedback
    
    # Cleanup
    if os.path.exists(feedback.FEEDBACK_DIR):
        shutil.rmtree(feedback.FEEDBACK_DIR)


def test_record_feedback(feedback_system) -> None:
    """Test recording feedback."""
    record = feedback_system.record_feedback(
        incident_id="inc-1",
        predicted_severity="P1",
        actual_severity="P2",
        user_comments="Good but slightly too severe",
        is_accurate=False,
    )
    
    assert record["incident_id"] == "inc-1"
    assert record["predicted_severity"] == "P1"
    assert record["actual_severity"] == "P2"
    assert record["correction_made"] is True
    assert record["is_accurate"] is False


def test_accurate_feedback(feedback_system) -> None:
    """Test recording accurate feedback."""
    record = feedback_system.record_feedback(
        incident_id="inc-1",
        predicted_severity="P2",
        is_accurate=True,
    )
    
    assert record["is_accurate"] is True
    assert record["correction_made"] is False
    assert record["actual_severity"] is None


def test_metrics_update(feedback_system) -> None:
    """Test that metrics are updated after feedback."""
    feedback_system.record_feedback(
        incident_id="inc-1",
        predicted_severity="P1",
        is_accurate=True,
    )
    
    metrics = feedback_system.get_metrics()
    
    assert metrics["total_feedback"] == 1
    assert metrics["accurate_predictions"] == 1
    assert metrics["overall_accuracy"] == 1.0


def test_correction_rate(feedback_system) -> None:
    """Test correction rate calculation."""
    # Record one correct prediction
    feedback_system.record_feedback(
        incident_id="inc-1",
        predicted_severity="P1",
        is_accurate=True,
    )
    
    # Record one incorrect prediction with correction
    feedback_system.record_feedback(
        incident_id="inc-2",
        predicted_severity="P1",
        actual_severity="P3",
        is_accurate=False,
    )
    
    metrics = feedback_system.get_metrics()
    
    assert metrics["total_feedback"] == 2
    assert metrics["accurate_predictions"] == 1
    assert metrics["corrections"] == 1
    assert metrics["correction_rate"] == 0.5
    assert metrics["overall_accuracy"] == 0.5


def test_get_feedback_records(feedback_system) -> None:
    """Test retrieving feedback records."""
    # Add multiple records
    for i in range(3):
        feedback_system.record_feedback(
            incident_id=f"inc-{i}",
            predicted_severity="P1",
            is_accurate=True,
        )
    
    records = feedback_system.get_feedback_records()
    
    assert len(records) == 3
    assert all("incident_id" in r for r in records)


def test_feedback_limit(feedback_system) -> None:
    """Test limiting feedback retrieval."""
    for i in range(5):
        feedback_system.record_feedback(
            incident_id=f"inc-{i}",
            predicted_severity="P1",
            is_accurate=True,
        )
    
    records = feedback_system.get_feedback_records(limit=2)
    
    assert len(records) == 2


def test_get_feedback_by_incident(feedback_system) -> None:
    """Test retrieving feedback for specific incident."""
    feedback_system.record_feedback(
        incident_id="inc-1",
        predicted_severity="P1",
        is_accurate=True,
    )
    
    feedback_system.record_feedback(
        incident_id="inc-2",
        predicted_severity="P2",
        is_accurate=False,
    )
    
    records = feedback_system.get_feedback_by_incident("inc-1")
    
    assert len(records) == 1
    assert records[0]["incident_id"] == "inc-1"


def test_false_positives(feedback_system) -> None:
    """Test identifying false positives."""
    # False positive: predicted P1 but actually P4
    feedback_system.record_feedback(
        incident_id="inc-1",
        predicted_severity="P1",
        actual_severity="P4",
        is_accurate=False,
    )
    
    # Correct classification
    feedback_system.record_feedback(
        incident_id="inc-2",
        predicted_severity="P1",
        actual_severity="P1",
        is_accurate=True,
    )
    
    false_positives = feedback_system.get_false_positives()
    
    assert len(false_positives) == 1
    assert false_positives[0]["incident_id"] == "inc-1"


def test_false_negatives(feedback_system) -> None:
    """Test identifying false negatives."""
    # False negative: predicted P4 but actually P1
    feedback_system.record_feedback(
        incident_id="inc-1",
        predicted_severity="P4",
        actual_severity="P1",
        is_accurate=False,
    )
    
    # Correct classification
    feedback_system.record_feedback(
        incident_id="inc-2",
        predicted_severity="P4",
        actual_severity="P4",
        is_accurate=True,
    )
    
    false_negatives = feedback_system.get_false_negatives()
    
    assert len(false_negatives) == 1
    assert false_negatives[0]["incident_id"] == "inc-1"


def test_clear_feedback(feedback_system) -> None:
    """Test clearing feedback data."""
    feedback_system.record_feedback(
        incident_id="inc-1",
        predicted_severity="P1",
        is_accurate=True,
    )
    
    assert len(feedback_system.get_feedback_records()) > 0
    
    feedback_system.clear_feedback()
    
    assert len(feedback_system.get_feedback_records()) == 0
    assert feedback_system.get_metrics()["total_feedback"] == 0
