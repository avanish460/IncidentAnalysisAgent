from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

SERVICE_NAMES = [
    "payments",
    "auth",
    "orders",
    "inventory",
    "search",
    "notifications",
    "analytics",
]

COMPONENT_NAMES = [
    "app-server-1",
    "app-server-2",
    "db-primary",
    "db-replica",
    "cache-node-1",
    "cache-node-2",
    "api-gateway",
]

SEVERITIES = ["critical", "high", "medium", "low"]

SCENARIO_ALERTS = {
    "normal": [
        ("low", "Minor latency increase detected"),
        ("medium", "Request latency above threshold"),
    ],
    "degradation": [
        ("high", "CPU usage exceeded threshold"),
        ("high", "Memory utilization is dangerously high"),
        ("medium", "Service timeout rate increased"),
    ],
    "outage": [
        ("critical", "Service unavailable due to repeated errors"),
        ("critical", "Database connection pool exhausted"),
        ("high", "API gateway requests are timing out"),
    ],
}

TICKET_DESCRIPTIONS = [
    "Customers are observing timeouts and failed transactions.",
    "Monitoring shows an increase in HTTP 5xx errors.",
    "The service is returning authentication errors for valid users.",
    "Database latency has increased, causing timeouts.",
    "Performance degradation has been detected across multiple regions.",
    "A service dependency appears to be failing intermittently.",
]

TICKET_SUMMARIES = [
    "Production service is degraded",
    "Users cannot complete checkout",
    "Authentication failures observed",
    "High error rate in backend API",
    "Database connection failures",
]

SOURCE_TYPE_MAP = {
    "prometheus": "prometheus-alerts",
    "datadog": "datadog-alerts",
    "cloudwatch": "cloudwatch-alerts",
    "servicenow": "servicenow-monitor",
    "jira": "jira-monitor",
    "splunk": "splunk-indexer",
    "mock": "mock-monitor",
}


def _random_id(prefix: str, length: int = 6) -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}-{suffix}"


def _timestamp(minutes_back: int = 5) -> str:
    return (datetime.utcnow() - timedelta(minutes=random.randint(0, minutes_back))).isoformat()


def _build_alert_message(severity: str, connector_type: str, service: str) -> str:
    if connector_type in {"prometheus", "datadog", "cloudwatch"}:
        return f"{service} service reported {severity} severity event"
    return f"{service} infrastructure event: {severity} alert"


def generate_simulated_alerts(
    connector_type: str = "mock",
    scenario: str = "degradation",
    count: int = 6,
    since_minutes: int = 30,
) -> List[Dict[str, Any]]:
    """Generate simulated alerts for a connector type and scenario."""
    connector_type = connector_type.lower()
    scenario = scenario if scenario in SCENARIO_ALERTS else "degradation"
    alerts: List[Dict[str, Any]] = []

    for i in range(count):
        severity, snippet = random.choice(SCENARIO_ALERTS[scenario])
        service = random.choice(SERVICE_NAMES)
        source = SOURCE_TYPE_MAP.get(connector_type, "simulator")
        if connector_type == "mock":
            source = random.choice(COMPONENT_NAMES)

        alerts.append(
            {
                "id": _random_id("A"),
                "source": source,
                "severity": severity,
                "message": _build_alert_message(severity, connector_type, service)
                if random.random() > 0.25
                else snippet,
                "timestamp": _timestamp(since_minutes),
                "metadata": {
                    "service": service,
                    "source_type": connector_type,
                    "scenario": scenario,
                },
            }
        )

    if scenario == "outage":
        # Ensure at least one critical alert exists for outage scenarios
        if not any(alert["severity"] == "critical" for alert in alerts):
            alerts[0]["severity"] = "critical"
            alerts[0]["message"] = f"Critical outage detected in {alerts[0]['metadata']['service']}"

    return alerts


def generate_simulated_tickets(
    connector_type: str = "mock",
    scenario: str = "degradation",
    alerts: Optional[List[Dict[str, Any]]] = None,
    count: int = 3,
) -> List[Dict[str, Any]]:
    """Generate simulated tickets correlated to synthetic alerts."""
    tickets: List[Dict[str, Any]] = []
    base_time = datetime.utcnow()
    service_names = []

    if alerts:
        for alert in alerts:
            service = alert.get("metadata", {}).get("service")
            if service:
                service_names.append(service)

    service_names = service_names or random.sample(SERVICE_NAMES, min(count, len(SERVICE_NAMES)))

    for i in range(count):
        current_service = service_names[i % len(service_names)]
        summary = random.choice(TICKET_SUMMARIES)
        description = random.choice(TICKET_DESCRIPTIONS)
        priority = "critical" if scenario == "outage" and i == 0 else random.choice(["high", "medium", "low"])

        tickets.append(
            {
                "id": _random_id("T"),
                "system": connector_type if connector_type != "mock" else "MockSystem",
                "category": "incident" if priority in {"critical", "high"} else "service request",
                "priority": priority,
                "summary": summary,
                "description": f"{description} Affected service: {current_service}.",
                "created_at": (base_time - timedelta(minutes=i * 15)).isoformat(),
                "metadata": {
                    "service": current_service,
                    "connector": connector_type,
                    "scenario": scenario,
                },
            }
        )

    return tickets
