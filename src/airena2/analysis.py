from __future__ import annotations

from typing import List, Optional

from .data_models import IncidentEvent

try:
    from .llm_engine import LLMEngine
except ImportError:  # pragma: no cover
    LLMEngine = None

try:
    from .ml_classifier import MLIncidentClassifier
except ImportError:
    MLIncidentClassifier = None

try:
    from .correlation import SemanticCorrelationEngine
except ImportError:
    SemanticCorrelationEngine = None

try:
    from .summarization import AdvancedSummarizationEngine
except ImportError:
    AdvancedSummarizationEngine = None

try:
    from .feedback import FeedbackCapture
except ImportError:
    FeedbackCapture = None


class AnalysisEngine:
    """Advanced incident analysis with ML, semantic correlation, and LLM integration."""

    def __init__(self, model: str = "gpt-4") -> None:
        # LLM Engine for advanced analysis
        self.llm: Optional[LLMEngine] = None
        self.llm_enabled = False
        if LLMEngine is not None:
            try:
                self.llm = LLMEngine(model=model)
                self.llm_enabled = True
                print("[INFO] OpenAI LLM integration enabled.")
            except ValueError:
                self.llm = None
                self.llm_enabled = False
        
        # ML Classifier for severity/impact prediction
        self.classifier: Optional[MLIncidentClassifier] = None
        if MLIncidentClassifier is not None:
            try:
                self.classifier = MLIncidentClassifier()
                if self.classifier.ml_enabled:
                    print("[INFO] ML-based classification enabled.")
            except Exception as e:
                print(f"[WARN] ML classifier initialization failed: {e}")
        
        # Semantic Correlation for alert grouping
        self.correlator: Optional[SemanticCorrelationEngine] = None
        if SemanticCorrelationEngine is not None:
            try:
                self.correlator = SemanticCorrelationEngine()
                print("[INFO] Semantic correlation engine enabled.")
            except Exception as e:
                print(f"[WARN] Semantic correlation initialization failed: {e}")
        
        # Advanced Summarization Engine
        self.summarizer: Optional[AdvancedSummarizationEngine] = None
        if AdvancedSummarizationEngine is not None:
            try:
                self.summarizer = AdvancedSummarizationEngine()
                if self.summarizer.is_available:
                    print("[INFO] Advanced summarization engine enabled.")
            except Exception as e:
                print(f"[WARN] Summarization engine initialization failed: {e}")
        
        # Feedback Capture for continuous learning
        self.feedback: Optional[FeedbackCapture] = None
        if FeedbackCapture is not None:
            try:
                self.feedback = FeedbackCapture()
                print("[INFO] Feedback capture system enabled.")
            except Exception as e:
                print(f"[WARN] Feedback capture initialization failed: {e}")

    def summarize_incident(self, incident: IncidentEvent) -> str:
        """Generate incident summary using multiple strategies.
        
        Args:
            incident: IncidentEvent to summarize
            
        Returns:
            Incident summary text
        """
        # Try LLM first (best quality)
        if self.llm is not None:
            try:
                return self.llm.summarize_incident(incident)
            except Exception as exc:
                print(f"[WARN] LLM summarization failed: {exc}")
        
        # Try advanced transformer-based summarization
        if self.summarizer is not None and self.summarizer.is_available:
            try:
                return self.summarizer.generate_detailed_summary(incident)
            except Exception as exc:
                print(f"[WARN] Transformer summarization failed: {exc}")
        
        # Fallback to rule-based summary
        return self._summarize_incident_fallback(incident)

    def _summarize_incident_fallback(self, incident: IncidentEvent) -> str:
        """Rule-based fallback summarization."""
        title = incident.title
        severity = incident.severity
        alert_count = len(incident.alerts)
        ticket_count = len(incident.tickets)
        
        summary = (
            f"{title} with severity {severity}. "
            f"The incident includes {alert_count} alert(s) and {ticket_count} ticket(s)."
        )
        
        # Add key points if available
        if self.summarizer is not None:
            try:
                key_points = self.summarizer.extract_key_points(incident)
                if key_points:
                    summary += " Key observations: " + "; ".join(key_points)
            except Exception:
                pass
        
        return summary

    def generate_rca(self, incident: IncidentEvent) -> str:
        """Generate root cause analysis using multiple strategies.
        
        Args:
            incident: IncidentEvent to analyze
            
        Returns:
            Root cause analysis text
        """
        # Try LLM first (best quality)
        if self.llm is not None:
            try:
                return self.llm.generate_rca(incident)
            except Exception as exc:
                print(f"[WARN] LLM RCA generation failed: {exc}")
        
        # Fallback to pattern-based RCA
        return self._generate_rca_fallback(incident)

    def _generate_rca_fallback(self, incident: IncidentEvent) -> str:
        """Pattern-based fallback RCA generation."""
        alert_count = incident.metadata.get("alert_count", len(incident.alerts))
        
        # Analyze alert patterns
        error_types = []
        for alert in incident.alerts:
            msg = alert.message.lower()
            if "cpu" in msg or "memory" in msg:
                error_types.append("resource exhaustion")
            elif "connection" in msg or "timeout" in msg:
                error_types.append("connectivity issues")
            elif "database" in msg:
                error_types.append("database failures")
            elif "error" in msg or "failed" in msg:
                error_types.append("application errors")
        
        unique_errors = list(set(error_types))
        
        if len(unique_errors) > 1:
            return f"Multiple failure modes detected: {', '.join(unique_errors)}. Suggests cascading failure or system overload."
        elif unique_errors:
            return f"Primary issue identified as {unique_errors[0]}. Investigate system components related to this failure mode."
        elif alert_count > 1:
            return "Multiple related alerts suggest a service dependency issue or distributed failure."
        else:
            return "Single alert indicates a targeted service or component fault."

    def recommend_actions(self, incident: IncidentEvent) -> List[str]:
        """Generate actionable recommendations using multiple strategies.
        
        Args:
            incident: IncidentEvent to analyze
            
        Returns:
            List of recommended actions
        """
        # Try LLM first (best quality)
        if self.llm is not None:
            try:
                return self.llm.recommend_actions(incident)
            except Exception as exc:
                print(f"[WARN] LLM recommendations failed: {exc}")
        
        # Fallback to rule-based recommendations
        return self._recommend_actions_fallback(incident)

    def _recommend_actions_fallback(self, incident: IncidentEvent) -> List[str]:
        """Rule-based fallback recommendation generation."""
        recommendations: List[str] = []
        
        # Primary action based on severity
        if incident.severity == "P1":
            recommendations.append("URGENT: Activate incident commander and war room.")
            recommendations.append("Execute critical incident runbook for this service.")
            recommendations.append("Notify on-call team and management immediately.")
        elif incident.severity == "P2":
            recommendations.append("Notify the on-call engineer for this service.")
            recommendations.append("Review recent deployments and configuration changes.")
        
        # Generic investigation steps
        recommendations.append("Collect recent logs from affected components.")
        recommendations.append("Check service health dashboards and metrics.")
        
        # Service-specific recommendations
        alert_messages = " ".join([a.message.lower() for a in incident.alerts])
        
        if "cpu" in alert_messages or "memory" in alert_messages:
            recommendations.append("Investigate resource utilization; consider scaling if needed.")
        if "database" in alert_messages or "connection" in alert_messages:
            recommendations.append("Verify database connectivity and check for connection pool exhaustion.")
        if "timeout" in alert_messages:
            recommendations.append("Review service latency and timeout configurations.")
        if "error" in alert_messages:
            recommendations.append("Examine application error logs for stack traces and patterns.")
        
        # Generic closing
        if incident.severity in {"P1", "P2"}:
            recommendations.append("Update status page and communicate with stakeholders.")
        
        return recommendations

    def refine_incident_classification(self, incident: IncidentEvent) -> None:
        """Use ML classifier to refine incident severity/impact if available.
        
        Args:
            incident: IncidentEvent to refine
        """
        if self.classifier is None or not self.classifier.ml_enabled:
            return
        
        try:
            # Update severity using ML classifier
            ml_severity = self.classifier.classify_severity(incident)
            if ml_severity != incident.severity:
                print(f"[INFO] ML classifier suggests severity: {ml_severity} (was {incident.severity})")
                # Could update incident.severity here, but keeping original for comparison
            
            # Update impact using ML classifier
            ml_impact = self.classifier.classify_impact(incident)
            if ml_impact != incident.classification:
                print(f"[INFO] ML classifier suggests impact: {ml_impact} (was {incident.classification})")
        except Exception as e:
            print(f"[WARN] ML classification refinement failed: {e}")

    def record_feedback(
        self,
        incident: IncidentEvent,
        actual_severity: Optional[str] = None,
        user_comments: str = "",
    ) -> None:
        """Record feedback on incident classification for model improvement.
        
        Args:
            incident: IncidentEvent to record feedback for
            actual_severity: User's corrected severity (if different)
            user_comments: Additional comments
        """
        if self.feedback is None:
            return
        
        is_accurate = actual_severity is None
        self.feedback.record_feedback(
            incident_id=incident.id,
            predicted_severity=incident.severity,
            actual_severity=actual_severity,
            predicted_impact=incident.classification,
            user_comments=user_comments,
            is_accurate=is_accurate,
        )
