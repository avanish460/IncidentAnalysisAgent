from datetime import datetime

from airena2.data_models import AlertRecord
from airena2.service_topology import ServiceTopology


def test_analyze_impacted_services_from_alert_metadata():
    topology = ServiceTopology()
    alerts = [
        AlertRecord(
            id="A1",
            source="prometheus-alerts",
            severity="critical",
            message="payments service is unavailable",
            timestamp=datetime.utcnow(),
            metadata={"service": "payments"},
        ),
        AlertRecord(
            id="A2",
            source="datadog-alerts",
            severity="high",
            message="auth service latency spike",
            timestamp=datetime.utcnow(),
            metadata={"service": "auth"},
        ),
    ]

    impacted = topology.analyze_impacted_services(alerts)
    assert "payments" in impacted
    assert "auth" in impacted
    assert len(impacted) == 2
