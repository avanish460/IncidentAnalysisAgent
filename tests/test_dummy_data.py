from airena2.dummy_data import generate_dummy_alerts, generate_dummy_tickets


def test_generate_dummy_alerts_count() -> None:
    alerts = generate_dummy_alerts(12)
    assert len(alerts) == 12
    assert all("id" in alert and "source" in alert and "severity" in alert for alert in alerts)


def test_generate_dummy_tickets_count() -> None:
    tickets = generate_dummy_tickets(5)
    assert len(tickets) == 5
    assert all("id" in ticket and "summary" in ticket and "description" in ticket for ticket in tickets)
