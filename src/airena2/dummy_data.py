from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List


SERVICE_NAMES = [
    "payments", "orders", "auth", "inventory", "search", "notifications", "analytics"
]

ALERT_SOURCES = [
    "app-server-1", "app-server-2", "db-primary", "db-replica", "cache-node-1", "api-gateway"
]

SEVERITIES = ["critical", "high", "medium", "low"]

TICKET_PRIORITIES = ["critical", "high", "medium", "low"]

TICKET_CATEGORIES = ["incident", "service request", "change", "problem"]

ALERT_MESSAGES = [
    "CPU usage exceeded threshold",
    "Request latency above SLA",
    "Error rate spike detected",
    "Database connection failures",
    "Memory utilization is dangerously high",
    "Cluster nodes are becoming unavailable",
    "Service timeout rate increased",
]

TICKET_SUMMARIES = [
    "Production service is degraded",
    "Users cannot complete checkout",
    "Authentication failures observed",
    "High error rate in backend API",
    "Scheduled maintenance request",
    "Unexpected traffic surge caused failures",
]

TICKET_DESCRIPTIONS = [
    "Customers are observing timeouts and failed transactions.",
    "Monitoring shows an increase in HTTP 5xx errors.",
    "The service is returning authentication errors for valid users.",
    "Database latency has increased, causing timeouts.",
    "Performance degradation has been detected across multiple regions.",
    "A service dependency appears to be failing intermittently.",
]


def _random_id(prefix: str, length: int = 6) -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}-{suffix}"


def _random_timestamp(hours_back: int = 6) -> str:
    return (datetime.utcnow() - timedelta(minutes=random.randint(0, hours_back * 60))).isoformat()


def generate_dummy_alerts(count: int = 10) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for _ in range(count):
        service = random.choice(SERVICE_NAMES)
        alerts.append(
            {
                "id": _random_id("A"),
                "source": random.choice(ALERT_SOURCES),
                "severity": random.choices(SEVERITIES, weights=(10, 25, 40, 25), k=1)[0],
                "message": random.choice(ALERT_MESSAGES),
                "timestamp": _random_timestamp(),
                "metadata": {"service": service, "region": random.choice(["us-east-1", "eu-west-1", "ap-south-1"])}
            }
        )
    return alerts


def generate_dummy_tickets(count: int = 5) -> List[Dict[str, Any]]:
    tickets: List[Dict[str, Any]] = []
    for _ in range(count):
        tickets.append(
            {
                "id": _random_id("T"),
                "system": random.choice(["ServiceNow", "Jira", "Zendesk"]),
                "category": random.choice(TICKET_CATEGORIES),
                "priority": random.choices(TICKET_PRIORITIES, weights=(10, 25, 40, 25), k=1)[0],
                "summary": random.choice(TICKET_SUMMARIES),
                "description": random.choice(TICKET_DESCRIPTIONS),
                "created_at": _random_timestamp(24),
                "metadata": {"assignee": random.choice(["ops-team", "infra-team", "app-team"])}
            }
        )
    return tickets


def generate_dummy_dataset(alert_count: int = 10, ticket_count: int = 3) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    return generate_dummy_alerts(alert_count), generate_dummy_tickets(ticket_count)
