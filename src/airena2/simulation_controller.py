"""Phase 3 simulation orchestrator."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .connectors import create_connector
from .incident_manager import IncidentStore
from .pipeline import AIPipeline
from .service_topology import ServiceTopology


class SimulationController:
    """Orchestrates Phase 3 simulations end-to-end."""

    def __init__(
        self,
        pipeline: AIPipeline,
        incident_store: IncidentStore,
        service_topology: ServiceTopology,
    ) -> None:
        self.pipeline = pipeline
        self.incident_store = incident_store
        self.service_topology = service_topology

    def run_simulation(
        self,
        connector_type: str = "mock",
        scenario: str = "degradation",
        analyze: bool = True,
        store_result: bool = True,
    ) -> Dict[str, Any]:
        """Run a complete simulation from data generation through analysis.

        Args:
            connector_type: Connector to use (mock, prometheus, etc.)
            scenario: Simulation scenario (normal, degradation, outage)
            analyze: Whether to run analysis pipeline
            store_result: Whether to store incident result

        Returns:
            Complete simulation result with analysis
        """
        # Step 1: Fetch simulated data
        try:
            connector = create_connector(connector_type, scenario=scenario)
            if not connector.test_connection():
                return {"status": "failed", "reason": f"Cannot connect to {connector_type}"}

            alerts = connector.fetch_alerts()
            tickets = connector.fetch_tickets()
        except Exception as e:
            return {"status": "failed", "reason": f"Data fetch error: {str(e)}"}

        # Step 2: Convert to dict format for pipeline
        alert_dicts = [
            {
                "id": alert["id"],
                "source": alert["source"],
                "severity": alert["severity"],
                "message": alert["message"],
                "timestamp": alert["timestamp"],
                "metadata": alert["metadata"],
            }
            for alert in alerts
        ]

        ticket_dicts = [
            {
                "id": ticket["id"],
                "system": ticket["system"],
                "category": ticket["category"],
                "priority": ticket["priority"],
                "summary": ticket["summary"],
                "description": ticket["description"],
                "created_at": ticket["created_at"],
                "metadata": ticket["metadata"],
            }
            for ticket in tickets
        ]

        # Step 3: Run analysis if requested
        incident = None
        impacted_services: List[str] = []

        if analyze:
            try:
                incident = self.pipeline.run(alert_dicts, ticket_dicts)
                impacted_services = self.service_topology.analyze_impacted_services(
                    incident.alerts
                )
                incident.metadata["impacted_services"] = impacted_services

                # Step 4: Store result if requested
                if store_result:
                    self.incident_store.add_incident(
                        incident,
                        processed_at=datetime.utcnow().isoformat(),
                        impacted_services=impacted_services,
                    )
            except Exception as e:
                return {"status": "failed", "reason": f"Analysis error: {str(e)}"}

        # Step 5: Return complete result
        return {
            "status": "success",
            "simulation": {
                "connector_type": connector_type,
                "scenario": scenario,
                "alert_count": len(alerts),
                "ticket_count": len(tickets),
            },
            "analysis": (
                {
                    "incident_id": incident.id,
                    "title": incident.title,
                    "severity": incident.severity,
                    "classification": incident.classification,
                    "summary": incident.summary,
                    "rca": incident.rca,
                    "recommendations": incident.recommendations,
                    "impacted_services": impacted_services,
                    "processed_at": datetime.utcnow().isoformat(),
                }
                if incident
                else None
            ),
        }

    def run_scenario_batch(
        self,
        scenarios: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Run multiple scenarios for demonstration/testing.

        Args:
            scenarios: List of scenario configs. If None, uses default set.

        Returns:
            Batch results with all scenarios executed
        """
        if scenarios is None:
            scenarios = [
                {"connector_type": "prometheus", "scenario": "normal"},
                {"connector_type": "datadog", "scenario": "degradation"},
                {"connector_type": "cloudwatch", "scenario": "outage"},
            ]

        results = []
        for scenario_config in scenarios:
            result = self.run_simulation(
                connector_type=scenario_config.get("connector_type", "mock"),
                scenario=scenario_config.get("scenario", "degradation"),
                analyze=True,
                store_result=True,
            )
            results.append(result)

        return {
            "batch_status": "completed",
            "scenarios_executed": len(results),
            "results": results,
            "incident_count": self.incident_store.count(),
            "timestamp": datetime.utcnow().isoformat(),
        }
