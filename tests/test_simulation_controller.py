"""Tests for Phase 3 simulation controller."""

from airena2.feedback import FeedbackCapture
from airena2.incident_manager import IncidentStore
from airena2.pipeline import AIPipeline
from airena2.service_topology import ServiceTopology
from airena2.simulation_controller import SimulationController


def test_simulation_controller_run_simulation_success():
    pipeline = AIPipeline()
    incident_store = IncidentStore()
    service_topology = ServiceTopology()
    controller = SimulationController(pipeline, incident_store, service_topology)

    result = controller.run_simulation(
        connector_type="mock",
        scenario="degradation",
        analyze=True,
        store_result=True,
    )

    assert result["status"] == "success"
    assert "simulation" in result
    assert result["simulation"]["alert_count"] > 0
    assert result["simulation"]["ticket_count"] > 0
    assert "analysis" in result
    if result["analysis"]:
        assert "incident_id" in result["analysis"]
        assert "severity" in result["analysis"]
        assert "impacted_services" in result["analysis"]


def test_simulation_controller_stores_incident():
    pipeline = AIPipeline()
    incident_store = IncidentStore()
    service_topology = ServiceTopology()
    controller = SimulationController(pipeline, incident_store, service_topology)

    initial_count = incident_store.count()

    result = controller.run_simulation(
        connector_type="prometheus",
        scenario="outage",
        analyze=True,
        store_result=True,
    )

    assert result["status"] == "success"
    assert incident_store.count() > initial_count


def test_simulation_controller_run_scenario_batch():
    pipeline = AIPipeline()
    incident_store = IncidentStore()
    service_topology = ServiceTopology()
    controller = SimulationController(pipeline, incident_store, service_topology)

    scenarios = [
        {"connector_type": "mock", "scenario": "normal"},
        {"connector_type": "datadog", "scenario": "degradation"},
    ]

    result = controller.run_scenario_batch(scenarios=scenarios)

    assert result["batch_status"] == "completed"
    assert result["scenarios_executed"] == 2
    assert len(result["results"]) == 2
    assert all(r["status"] == "success" for r in result["results"])
