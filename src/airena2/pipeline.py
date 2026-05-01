from __future__ import annotations

from typing import Iterable, List

from .analysis import AnalysisEngine
from .data_ingest import DataIngestor
from .data_models import AlertRecord, IncidentEvent, TicketRecord
from .reporting import ReportGenerator
from .triage import TriageEngine


class AIPipeline:
    """End-to-end orchestration for incident analysis."""

    def __init__(self) -> None:
        self.ingestor = DataIngestor()
        self.triage = TriageEngine()
        self.analysis = AnalysisEngine()
        self.reporter = ReportGenerator()

    def run(self, alert_data: Iterable[dict], ticket_data: Iterable[dict]) -> IncidentEvent:
        if self.analysis.llm_enabled:
            print("[INFO] Using OpenAI GPT-4 for incident analysis.")
        else:
            print("[INFO] OpenAI not available; using local fallback analysis.")

        alerts: List[AlertRecord] = self.ingestor.load_alerts(alert_data)
        tickets: List[TicketRecord] = self.ingestor.load_tickets(ticket_data)
        incident = self.triage.build_incident(alerts, tickets)
        incident.summary = self.analysis.summarize_incident(incident)
        incident.rca = self.analysis.generate_rca(incident)
        incident.recommendations = self.analysis.recommend_actions(incident)
        self.reporter.print_report(incident)
        return incident
