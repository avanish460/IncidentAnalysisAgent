from datetime import datetime

from airena2.pipeline import AIPipeline


def test_pipeline_runs_with_sample_data() -> None:
    pipeline = AIPipeline()
    alert_data = [
        {
            "id": "A-1001",
            "source": "db-cluster",
            "severity": "high",
            "message": "Database connection error",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"region": "us-east-1"},
        }
    ]
    ticket_data = [
        {
            "id": "T-3001",
            "system": "Jira",
            "category": "incident",
            "priority": "high",
            "summary": "DB connection failures",
            "description": "Users report intermittent database connection failures.",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {"team": "platform"},
        }
    ]

    incident = pipeline.run(alert_data, ticket_data)

    assert incident.id.startswith("incident-")
    assert incident.summary is not None
    assert incident.rca is not None
    assert incident.recommendations
