from __future__ import annotations

import argparse
from datetime import datetime

from .connectors import create_connector
from .dummy_data import generate_dummy_dataset
from .pipeline import AIPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AIrena2.0 starter pipeline.")
    parser.add_argument("--sample", action="store_true", help="Use sample incident data.")
    parser.add_argument("--dummy", action="store_true", help="Generate synthetic dummy data.")
    parser.add_argument("--simulate", action="store_true", help="Run Phase 3 simulation mode.")
    parser.add_argument("--alerts", type=int, default=8, help="Number of dummy alerts to generate.")
    parser.add_argument("--tickets", type=int, default=3, help="Number of dummy tickets to generate.")
    parser.add_argument("--api", action="store_true", help="Start the FastAPI server instead of running CLI pipeline.")
    parser.add_argument("--host", default="0.0.0.0", help="API server host (default: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=8000, help="API server port (default: 8000).")
    parser.add_argument("--connector", choices=["servicenow", "mock", "prometheus", "datadog", "cloudwatch", "jira", "splunk"], default="mock",
                       help="Data connector to use (default: mock).")
    parser.add_argument("--scenario", choices=["normal", "degradation", "outage"], default="degradation",
                       help="Scenario for simulated connectors.")
    parser.add_argument("--db", action="store_true", help="Enable database persistence (default: enabled).")
    parser.add_argument("--no-db", action="store_true", help="Disable database persistence.")
    parser.add_argument("--since", type=str, help="Fetch data since this datetime (ISO format).")
    return parser.parse_args()


def build_sample_data() -> tuple[list[dict], list[dict]]:
    alert_data = [
        {
            "id": "A-1001",
            "source": "app-server-1",
            "severity": "critical",
            "message": "CPU usage exceeded 95%",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"service": "payments"},
        }
    ]
    ticket_data = [
        {
            "id": "T-2001",
            "system": "ServiceNow",
            "category": "incident",
            "priority": "high",
            "summary": "Production payment service is degraded",
            "description": "Payments are timing out for customers and monitoring alerts show sustained high CPU.",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {"assignee": "ops-team"},
        }
    ]
    return alert_data, ticket_data


def build_dummy_data(alert_count: int, ticket_count: int) -> tuple[list[dict], list[dict]]:
    return generate_dummy_dataset(alert_count, ticket_count)


def run() -> None:
    args = parse_args()

    if args.api:
        # Start FastAPI server
        import uvicorn
        from .api import app
        print(f"Starting AIrena2.0 API server on {args.host}:{args.port}")
        print(f"API documentation available at: http://{args.host}:{args.port}/docs")
        uvicorn.run(app, host=args.host, port=args.port)
        return

    if args.simulate:
        # Phase 3: Run simulation mode
        from .feedback import FeedbackCapture
        from .incident_manager import IncidentStore
        from .service_topology import ServiceTopology
        from .simulation_controller import SimulationController

        use_db = not args.no_db
        print(f"Starting Phase 3 simulation (connector={args.connector}, scenario={args.scenario}, db={use_db})...")
        incident_store = IncidentStore(use_database=use_db)
        service_topology = ServiceTopology()
        feedback_capture = FeedbackCapture()
        pipeline = AIPipeline()
        controller = SimulationController(pipeline, incident_store, service_topology)

        result = controller.run_simulation(
            connector_type=args.connector,
            scenario=args.scenario,
            analyze=True,
            store_result=True,
        )

        if result.get("status") == "success":
            print("\n[SUCCESS] Phase 3 Simulation Complete")
            print(f"  Alerts: {result['simulation']['alert_count']}")
            print(f"  Tickets: {result['simulation']['ticket_count']}")
            if result.get("analysis"):
                analysis = result["analysis"]
                print(f"  Incident ID: {analysis['incident_id']}")
                print(f"  Severity: {analysis['severity']}")
                print(f"  Classification: {analysis['classification']}")
                print(f"  Impacted Services: {', '.join(analysis['impacted_services']) or 'None'}")
                print(f"  Summary: {analysis['summary'][:100]}..." if analysis.get("summary") else "  Summary: N/A")
            if use_db:
                print(f"  Total incidents in DB: {incident_store.count()}")
        else:
            print(f"\n[FAILED] {result.get('reason', 'Unknown error')}")
        return

    # CLI mode - run pipeline
    if args.sample:
        alerts, tickets = build_sample_data()
    elif args.dummy:
        alerts, tickets = build_dummy_data(args.alerts, args.tickets)
    else:
        # Use connector to fetch real data
        since = None
        if args.since:
            try:
                since = datetime.fromisoformat(args.since)
            except ValueError:
                print(f"Invalid datetime format: {args.since}. Use ISO format (e.g., 2024-01-15T10:00:00)")
                return

        try:
            connector = create_connector(args.connector, scenario=args.scenario)
            if not connector.test_connection():
                print(f"Failed to connect to {args.connector} data source")
                return

            print(f"Fetching data from {args.connector} (scenario={args.scenario})...")
            alerts = connector.fetch_alerts(since)
            tickets = connector.fetch_tickets(since)
            print(f"Fetched {len(alerts)} alerts and {len(tickets)} tickets")

        except ValueError as e:
            print(f"Connector error: {e}")
            return

    pipeline = AIPipeline()
    pipeline.run(alerts, tickets)


if __name__ == "__main__":
    run()
