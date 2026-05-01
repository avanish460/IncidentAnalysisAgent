from datetime import datetime

from airena2.data_models import IncidentEvent, AlertRecord, TicketRecord
from airena2.incident_manager import IncidentStore


def test_incident_store_add_and_retrieve():
    store = IncidentStore()
    event = IncidentEvent(
        id="INC-1001",
        title="Payment service outage",
        severity="critical",
        classification="incident",
        summary="Payments unavailable due to database failures.",
        rca="Database connectivity issues",
        recommendations=["Restart database cluster", "Scale the connection pool"],
        alerts=[
            AlertRecord(
                id="A1",
                source="app-server-1",
                severity="critical",
                message="payment service failed",
                timestamp=datetime.utcnow(),
                metadata={"service": "payments"},
            )
        ],
        tickets=[
            TicketRecord(
                id="T1",
                system="Jira",
                category="incident",
                priority="high",
                summary="Payment error rate elevated",
                description="Transaction failures observed.",
                created_at=datetime.utcnow(),
                metadata={"service": "payments"},
            )
        ],
        metadata={"source": "simulator"},
    )

    store.add_incident(event, processed_at=datetime.utcnow().isoformat(), impacted_services=["payments"])
    retrieved = store.get_incident("INC-1001")

    assert retrieved is not None
    assert retrieved["incident_id"] == "INC-1001"
    assert retrieved["alert_count"] == 1
    assert retrieved["ticket_count"] == 1
    assert "payments" in retrieved["impacted_services"]
