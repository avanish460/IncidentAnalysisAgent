from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

from .simulators import generate_simulated_alerts, generate_simulated_tickets


class DataConnector(ABC):
    """Abstract base class for external data source connectors."""

    @abstractmethod
    def fetch_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch alerts from the external system."""
        pass

    @abstractmethod
    def fetch_tickets(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch tickets from the external system."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connectivity to the external system."""
        pass


class ServiceNowConnector(DataConnector):
    """ServiceNow ITSM integration connector."""

    def __init__(self, instance_url: str, username: str, password: str):
        self.instance_url = instance_url.rstrip('/')
        self.username = username
        self.password = password
        self.base_url = f"{self.instance_url}/api/now"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def test_connection(self) -> bool:
        """Test connection to ServiceNow instance."""
        try:
            response = self.session.get(f"{self.base_url}/table/incident",
                                      params={'sysparm_limit': 1})
            return response.status_code == 200
        except Exception:
            return False

    def fetch_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Fetch alerts from ServiceNow.
        Note: ServiceNow doesn't have a native "alerts" table, so we'll fetch
        from incident table and filter for alert-like records.
        """
        # For now, return empty list as we don't have real ServiceNow access
        # In production, this would query ServiceNow tables
        return []

    def fetch_tickets(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch incidents from ServiceNow."""
        try:
            params = {
                'sysparm_limit': 100,
                'sysparm_fields': 'sys_id,number,short_description,description,priority,severity,opened_at,sys_created_by,assignment_group,incident_state'
            }

            if since:
                # Convert to ServiceNow datetime format
                since_str = since.strftime('%Y-%m-%d %H:%M:%S')
                params['sysparm_query'] = f'opened_at>={since_str}'

            response = self.session.get(f"{self.base_url}/table/incident", params=params)
            response.raise_for_status()

            incidents = response.json().get('result', [])
            return [self._parse_incident_to_dict(incident) for incident in incidents]

        except requests.RequestException as e:
            print(f"ServiceNow API error: {e}")
            return []

    def _parse_incident_to_dict(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ServiceNow incident into dictionary format."""
        # Map ServiceNow priority to our priority levels
        priority_map = {
            '1': 'critical',
            '2': 'high',
            '3': 'medium',
            '4': 'low',
            '5': 'low'
        }

        # Map ServiceNow severity to our severity levels
        severity_map = {
            '1': 'critical',
            '2': 'high',
            '3': 'medium',
            '4': 'low'
        }

        return {
            "id": incident.get('number', ''),
            "system": 'ServiceNow',
            "category": 'incident',
            "priority": priority_map.get(incident.get('priority', '3'), 'medium'),
            "summary": incident.get('short_description', ''),
            "description": incident.get('description', ''),
            "created_at": incident.get('opened_at', datetime.utcnow().isoformat()),
            "metadata": {
                'sys_id': incident.get('sys_id'),
                'severity': severity_map.get(incident.get('severity', '3'), 'medium'),
                'state': incident.get('incident_state'),
                'assigned_to': incident.get('sys_created_by'),
                'assignment_group': incident.get('assignment_group')
            }
        }


class SimulatorConnector(DataConnector):
    """Simulator connector for mock Phase 3 data sources."""

    def __init__(self, connector_type: str = "mock", scenario: str = "degradation") -> None:
        self.connector_type = connector_type.lower()
        self.scenario = scenario

    def test_connection(self) -> bool:
        return True

    def fetch_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return generate_simulated_alerts(
            connector_type=self.connector_type,
            scenario=self.scenario,
            count=8,
        )

    def fetch_tickets(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        alerts = self.fetch_alerts(since)
        return generate_simulated_tickets(
            connector_type=self.connector_type,
            scenario=self.scenario,
            alerts=alerts,
            count=3,
        )


class MockServiceNowConnector(DataConnector):
    """Mock ServiceNow connector for testing without real instance."""

    def __init__(self, instance_url: str = "https://mock.servicenow.com"):
        self.instance_url = instance_url

    def test_connection(self) -> bool:
        """Mock connection test - always succeeds."""
        return True

    def fetch_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Return mock alerts for testing."""
        return [
            {
                "id": "SN-ALERT-001",
                "source": "servicenow-monitor",
                "severity": "high",
                "message": "Multiple incidents reported in payment service",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"service": "payments", "count": 3}
            }
        ]

    def fetch_tickets(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Return mock ServiceNow incidents for testing."""
        return [
            {
                "id": "INC0012345",
                "system": "ServiceNow",
                "category": "incident",
                "priority": "high",
                "summary": "Payment service experiencing high error rates",
                "description": "Customers are unable to complete payments. Error rate has increased to 15% in the last hour. Multiple timeout errors observed in application logs.",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "sys_id": "mock-sys-id-123",
                    "severity": "2",
                    "state": "In Progress",
                    "assigned_to": "john.doe",
                    "assignment_group": "Payment Team"
                }
            },
            {
                "id": "INC0012346",
                "system": "ServiceNow",
                "category": "incident",
                "priority": "critical",
                "summary": "Database connection pool exhausted",
                "description": "Database connection pool has been exhausted for the payment database. This is causing cascading failures across the payment processing pipeline.",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "sys_id": "mock-sys-id-456",
                    "severity": "1",
                    "state": "New",
                    "assigned_to": "jane.smith",
                    "assignment_group": "Database Team"
                }
            }
        ]


def create_connector(connector_type: str = "mock", **kwargs) -> DataConnector:
    """
    Factory function to create data connectors.

    Args:
        connector_type: Type of connector ('servicenow', 'mock')
        **kwargs: Connector-specific parameters

    Returns:
        Configured data connector instance
    """
    connector_type = connector_type.lower()
    scenario = kwargs.get("scenario", "degradation")

    if connector_type == "servicenow":
        instance_url = kwargs.get('instance_url') or os.environ.get('SERVICENOW_INSTANCE_URL')
        username = kwargs.get('username') or os.environ.get('SERVICENOW_USERNAME')
        password = kwargs.get('password') or os.environ.get('SERVICENOW_PASSWORD')

        if not all([instance_url, username, password]):
            raise ValueError("ServiceNow connector requires instance_url, username, and password")

        return ServiceNowConnector(instance_url, username, password)

    elif connector_type == "mock":
        return SimulatorConnector('mock', scenario=scenario)

    elif connector_type in {"prometheus", "datadog", "cloudwatch", "jira", "splunk"}:
        return SimulatorConnector(connector_type, scenario=scenario)

    else:
        raise ValueError(f"Unknown connector type: {connector_type}")