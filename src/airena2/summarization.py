"""Advanced incident summarization using transformers."""

from __future__ import annotations

from typing import List, Optional

from .data_models import IncidentEvent

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class AdvancedSummarizationEngine:
    """Advanced summarization using transformer models."""

    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """Initialize summarization engine.
        
        Args:
            model_name: Transformer model to use (default: BART-large-CNN)
        """
        self.model_name = model_name
        self.summarizer = None
        self.is_available = TRANSFORMERS_AVAILABLE
        
        if self.is_available:
            try:
                self.summarizer = pipeline(
                    "summarization",
                    model=model_name,
                    device=-1  # Use CPU by default
                )
            except Exception as e:
                print(f"[WARN] Failed to load transformer model: {e}")
                self.is_available = False

    def _build_incident_text(self, incident: IncidentEvent) -> str:
        """Convert incident to text for summarization.
        
        Args:
            incident: IncidentEvent to convert
            
        Returns:
            Formatted text describing the incident
        """
        text_parts = []
        
        # Add incident overview
        text_parts.append(f"Incident: {incident.title}")
        text_parts.append(f"Severity: {incident.severity}")
        text_parts.append(f"Classification: {incident.classification}")
        text_parts.append("")
        
        # Add alert details
        if incident.alerts:
            text_parts.append("Alerts:")
            for alert in incident.alerts:
                text_parts.append(f"- [{alert.severity}] {alert.source}: {alert.message}")
            text_parts.append("")
        
        # Add ticket details
        if incident.tickets:
            text_parts.append("Tickets:")
            for ticket in incident.tickets:
                text_parts.append(f"- [{ticket.priority}] {ticket.summary}: {ticket.description}")
            text_parts.append("")
        
        return "\n".join(text_parts)

    def generate_brief_summary(self, incident: IncidentEvent) -> str:
        """Generate a brief executive summary.
        
        Args:
            incident: IncidentEvent to summarize
            
        Returns:
            Brief summary (1-2 sentences)
        """
        if not self.is_available:
            return self._generate_brief_summary_fallback(incident)
        
        text = self._build_incident_text(incident)
        
        try:
            # For brief summary, use max_length=30 tokens (~2 sentences)
            summary = self.summarizer(text, max_length=30, min_length=10, do_sample=False)
            return summary[0]["summary_text"]
        except Exception as e:
            print(f"[WARN] Transformer summarization failed: {e}")
            return self._generate_brief_summary_fallback(incident)

    def generate_detailed_summary(self, incident: IncidentEvent) -> str:
        """Generate a detailed technical summary.
        
        Args:
            incident: IncidentEvent to summarize
            
        Returns:
            Detailed summary (3-5 sentences)
        """
        if not self.is_available:
            return self._generate_detailed_summary_fallback(incident)
        
        text = self._build_incident_text(incident)
        
        try:
            # For detailed summary, use max_length=100 tokens (~4-5 sentences)
            summary = self.summarizer(text, max_length=100, min_length=30, do_sample=False)
            return summary[0]["summary_text"]
        except Exception as e:
            print(f"[WARN] Transformer summarization failed: {e}")
            return self._generate_detailed_summary_fallback(incident)

    def extract_key_points(self, incident: IncidentEvent) -> List[str]:
        """Extract key points from the incident.
        
        Args:
            incident: IncidentEvent to analyze
            
        Returns:
            List of key points
        """
        key_points = []
        
        # Add severity impact
        key_points.append(f"Severity level: {incident.severity}")
        
        # Add affected services
        services = set()
        for alert in incident.alerts:
            if "service" in alert.metadata:
                services.add(alert.metadata["service"])
        if services:
            key_points.append(f"Affected services: {', '.join(services)}")
        
        # Add error patterns
        error_keywords = ["error", "failed", "timeout", "exception"]
        alert_messages = [a.message for a in incident.alerts]
        for keyword in error_keywords:
            if any(keyword in msg.lower() for msg in alert_messages):
                key_points.append(f"Pattern detected: {keyword}s reported in alerts")
                break
        
        # Add ticket count
        if incident.tickets:
            key_points.append(f"Number of related tickets: {len(incident.tickets)}")
        
        return key_points

    def _generate_brief_summary_fallback(self, incident: IncidentEvent) -> str:
        """Fallback brief summary generation."""
        services = set()
        for alert in incident.alerts:
            if "service" in alert.metadata:
                services.add(alert.metadata["service"])
        
        service_str = f" in {', '.join(services)}" if services else ""
        alert_str = f" with {len(incident.alerts)} alert(s)" if incident.alerts else ""
        
        return f"Incident {incident.id} classified as {incident.severity}{service_str}{alert_str}."

    def _generate_detailed_summary_fallback(self, incident: IncidentEvent) -> str:
        """Fallback detailed summary generation."""
        parts = []
        
        # Overview
        parts.append(f"Incident {incident.id} is classified as {incident.severity} priority.")
        
        # Alert summary
        if incident.alerts:
            parts.append(f"Detected {len(incident.alerts)} alert(s) from systems: {', '.join(set(a.source for a in incident.alerts))}.")
        
        # Impact
        if incident.classification == "service-impact":
            parts.append("This incident has service-level impact and requires immediate attention.")
        else:
            parts.append("This is an informational incident for monitoring and tracking.")
        
        # Ticket summary
        if incident.tickets:
            parts.append(f"There are {len(incident.tickets)} related ticket(s) in the ticketing system.")
        
        return " ".join(parts)
