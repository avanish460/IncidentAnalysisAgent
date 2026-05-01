from __future__ import annotations

from typing import Dict

from .data_models import IncidentEvent


class ReportGenerator:
    """Format incident reports and export summaries."""

    def create_report(self, incident: IncidentEvent) -> Dict[str, object]:
        return {
            "incident_id": incident.id,
            "title": incident.title,
            "severity": incident.severity,
            "classification": incident.classification,
            "summary": incident.summary,
            "rca": incident.rca,
            "recommendations": incident.recommendations,
            "metadata": incident.metadata,
        }

    def print_report(self, incident: IncidentEvent) -> None:
        print("--- Incident Report ---")
        print(f"ID: {incident.id}")
        print(f"Title: {incident.title}")
        print(f"Severity: {incident.severity}")
        print(f"Classification: {incident.classification}")
        print(f"Summary: {incident.summary}")
        print(f"Root cause analysis: {incident.rca}")
        print("Recommendations:")
        for item in incident.recommendations or []:
            print(f" - {item}")
        print(f"Metadata: {incident.metadata}")
