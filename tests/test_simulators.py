from airena2.simulators import generate_simulated_alerts, generate_simulated_tickets


def test_generate_simulated_alerts_contains_service_metadata():
    alerts = generate_simulated_alerts(connector_type="prometheus", scenario="outage", count=4)
    assert isinstance(alerts, list)
    assert len(alerts) == 4
    for alert in alerts:
        assert "id" in alert
        assert "source" in alert
        assert "severity" in alert
        assert alert["metadata"]["service"]
        assert alert["metadata"]["source_type"] == "prometheus"


def test_generate_simulated_tickets_correlates_to_alerts():
    alerts = generate_simulated_alerts(connector_type="jira", scenario="degradation", count=3)
    tickets = generate_simulated_tickets(connector_type="jira", scenario="degradation", alerts=alerts, count=2)
    assert isinstance(tickets, list)
    assert len(tickets) == 2
    assert all("id" in ticket for ticket in tickets)
    assert all(ticket["metadata"]["connector"] == "jira" for ticket in tickets)
