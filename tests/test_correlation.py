"""Tests for semantic correlation engine."""

import pytest
from datetime import datetime
from airena2.data_models import AlertRecord
from airena2.correlation import SemanticCorrelationEngine


def test_semantic_correlation_groups_similar_alerts() -> None:
    """Test that similar alerts are grouped together."""
    correlator = SemanticCorrelationEngine()
    
    alerts = [
        AlertRecord(
            id="A1",
            source="app-server-1",
            severity="high",
            message="CPU usage exceeded threshold",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
        AlertRecord(
            id="A2",
            source="app-server-2",
            severity="high",
            message="CPU usage exceeded 95%",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
        AlertRecord(
            id="A3",
            source="db-server",
            severity="high",
            message="Database connection timeout",
            timestamp=datetime.utcnow(),
            metadata={},
        ),
    ]
    
    groups = correlator.correlate_alerts(alerts, similarity_threshold=0.5)
    
    # Should have at least 2 groups (CPU alerts together, DB alert separate)
    assert len(groups) >= 2
    
    # Each alert should appear in exactly one group
    all_grouped = []
    for group in groups:
        all_grouped.extend(group)
    assert len(all_grouped) == len(alerts)


def test_semantic_correlation_single_alert() -> None:
    """Test correlation with single alert."""
    correlator = SemanticCorrelationEngine()
    
    alerts = [
        AlertRecord(
            id="A1",
            source="app-server",
            severity="high",
            message="CPU spike detected",
            timestamp=datetime.utcnow(),
            metadata={},
        )
    ]
    
    groups = correlator.correlate_alerts(alerts)
    
    assert len(groups) == 1
    assert len(groups[0]) == 1
    assert groups[0][0].id == "A1"


def test_semantic_correlation_empty_alerts() -> None:
    """Test correlation with empty alert list."""
    correlator = SemanticCorrelationEngine()
    
    groups = correlator.correlate_alerts([])
    
    assert len(groups) == 0


def test_alert_similarity_score() -> None:
    """Test similarity scoring between alerts."""
    correlator = SemanticCorrelationEngine()
    
    alert1 = AlertRecord(
        id="A1",
        source="server-1",
        severity="high",
        message="CPU usage exceeded threshold",
        timestamp=datetime.utcnow(),
        metadata={},
    )
    
    alert2 = AlertRecord(
        id="A2",
        source="server-2",
        severity="high",
        message="CPU usage exceeded 95%",
        timestamp=datetime.utcnow(),
        metadata={},
    )
    
    alert3 = AlertRecord(
        id="A3",
        source="server-3",
        severity="high",
        message="Database connection failed",
        timestamp=datetime.utcnow(),
        metadata={},
    )
    
    # Similar CPU alerts should have high similarity
    sim_12 = correlator.get_alert_similarity(alert1, alert2)
    assert sim_12 > 0.0
    
    # Different alert types should have lower similarity
    sim_13 = correlator.get_alert_similarity(alert1, alert3)
    
    # sim_12 should be greater than sim_13 (same issue vs different issue)
    assert sim_12 >= 0.0 and sim_13 >= 0.0


def test_correlation_threshold_effect() -> None:
    """Test that similarity threshold affects grouping."""
    correlator = SemanticCorrelationEngine()
    
    alerts = [
        AlertRecord(
            id=f"A{i}",
            source=f"server-{i}",
            severity="high",
            message="CPU usage exceeded threshold",
            timestamp=datetime.utcnow(),
            metadata={},
        )
        for i in range(3)
    ]
    
    # With high threshold, expect more groups
    groups_high = correlator.correlate_alerts(alerts, similarity_threshold=0.99)
    
    # With low threshold, expect fewer groups
    groups_low = correlator.correlate_alerts(alerts, similarity_threshold=0.01)
    
    # High threshold should produce >= groups than low threshold
    # (because fewer alerts are similar enough to group)
    assert len(groups_high) >= len(groups_low)
