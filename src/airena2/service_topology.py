from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .data_models import AlertRecord


@dataclass
class ServiceDefinition:
    id: str
    name: str
    owner: str
    criticality: str
    description: str
    dependencies: List[str]


DEFAULT_SERVICE_REGISTRY: Dict[str, ServiceDefinition] = {
    "payments": ServiceDefinition(
        id="svc-payments",
        name="payments",
        owner="payments-team",
        criticality="critical",
        description="Handles customer payment processing and checkout flows.",
        dependencies=["auth", "database", "cache"],
    ),
    "auth": ServiceDefinition(
        id="svc-auth",
        name="auth",
        owner="auth-team",
        criticality="critical",
        description="Authentication and authorization service.",
        dependencies=["database"],
    ),
    "inventory": ServiceDefinition(
        id="svc-inventory",
        name="inventory",
        owner="inventory-team",
        criticality="high",
        description="Inventory and stock management service.",
        dependencies=["database"],
    ),
    "search": ServiceDefinition(
        id="svc-search",
        name="search",
        owner="search-team",
        criticality="high",
        description="Search service for product catalogs and orders.",
        dependencies=["cache", "database"],
    ),
    "notifications": ServiceDefinition(
        id="svc-notifications",
        name="notifications",
        owner="notifications-team",
        criticality="medium",
        description="Push and email notification delivery.",
        dependencies=["auth", "messaging"],
    ),
    "analytics": ServiceDefinition(
        id="svc-analytics",
        name="analytics",
        owner="analytics-team",
        criticality="medium",
        description="Analytics and reporting service.",
        dependencies=["database"],
    ),
}


class ServiceTopology:
    """Service dependency graph and incident impact analysis."""

    def __init__(self, services: Optional[Dict[str, ServiceDefinition]] = None) -> None:
        self.services = services or DEFAULT_SERVICE_REGISTRY

    def get_service(self, service_name: str) -> Optional[ServiceDefinition]:
        return self.services.get(service_name)

    def get_all_services(self) -> List[ServiceDefinition]:
        return list(self.services.values())

    def get_dependency_chain(self, service_name: str) -> List[str]:
        visited = set()
        chain: List[str] = []

        def walk(name: str) -> None:
            if name in visited or name not in self.services:
                return
            visited.add(name)
            chain.append(name)
            for dependency in self.services[name].dependencies:
                walk(dependency)

        walk(service_name)
        return chain

    def analyze_impacted_services(self, alerts: List[AlertRecord]) -> List[str]:
        impacted_services = set()
        for alert in alerts:
            service = alert.metadata.get("service")
            if isinstance(service, str) and service in self.services:
                impacted_services.add(service)

        if not impacted_services:
            # Fall back to search for known service names in alert messages
            for alert in alerts:
                message = alert.message.lower()
                for service_name in self.services.keys():
                    if service_name in message:
                        impacted_services.add(service_name)

        return sorted(impacted_services)

    def get_service_summary(self, service_name: str) -> Optional[Dict[str, object]]:
        service = self.get_service(service_name)
        if not service:
            return None
        return {
            "id": service.id,
            "name": service.name,
            "owner": service.owner,
            "criticality": service.criticality,
            "description": service.description,
            "dependencies": service.dependencies,
            "dependency_chain": self.get_dependency_chain(service_name),
        }
