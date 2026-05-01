"""Feedback capture and continuous learning system."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from .data_models import IncidentEvent


class FeedbackCapture:
    """Capture and store user feedback for model improvement."""

    FEEDBACK_DIR = ".airena2_feedback"
    FEEDBACK_FILE = os.path.join(FEEDBACK_DIR, "feedback.jsonl")
    METRICS_FILE = os.path.join(FEEDBACK_DIR, "metrics.json")

    def __init__(self):
        """Initialize feedback system."""
        self._ensure_feedback_dir()

    def _ensure_feedback_dir(self) -> None:
        """Ensure feedback directory exists."""
        os.makedirs(self.FEEDBACK_DIR, exist_ok=True)

    def record_feedback(
        self,
        incident_id: str,
        predicted_severity: str,
        actual_severity: Optional[str] = None,
        predicted_impact: str = "informational",
        actual_impact: Optional[str] = None,
        user_comments: str = "",
        is_accurate: bool = True,
    ) -> Dict[str, Any]:
        """Record feedback on an incident classification.
        
        Args:
            incident_id: ID of the incident
            predicted_severity: Model's predicted severity (P1-P4)
            actual_severity: User's corrected severity (optional)
            predicted_impact: Model's predicted impact classification
            actual_impact: User's corrected impact (optional)
            user_comments: Additional user comments
            is_accurate: Whether the prediction was accurate
            
        Returns:
            Feedback record
        """
        feedback_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "incident_id": incident_id,
            "predicted_severity": predicted_severity,
            "actual_severity": actual_severity,
            "predicted_impact": predicted_impact,
            "actual_impact": actual_impact,
            "user_comments": user_comments,
            "is_accurate": is_accurate,
            "correction_made": actual_severity is not None or actual_impact is not None,
        }
        
        # Append to feedback file
        try:
            with open(self.FEEDBACK_FILE, "a") as f:
                f.write(json.dumps(feedback_record) + "\n")
        except Exception as e:
            print(f"[WARN] Failed to write feedback: {e}")
        
        # Update metrics
        self._update_metrics(feedback_record)
        
        return feedback_record

    def _update_metrics(self, feedback: Dict[str, Any]) -> None:
        """Update overall feedback metrics.
        
        Args:
            feedback: Feedback record to incorporate
        """
        metrics = self.get_metrics()
        
        metrics["total_feedback"] += 1
        
        if feedback["is_accurate"]:
            metrics["accurate_predictions"] += 1
        else:
            metrics["inaccurate_predictions"] += 1
        
        if feedback["correction_made"]:
            metrics["corrections"] += 1
        
        # Track false positives/negatives
        if feedback["predicted_severity"] != feedback.get("actual_severity") and feedback.get("actual_severity"):
            metrics["severity_misclassifications"] += 1
        
        if feedback["predicted_impact"] != feedback.get("actual_impact") and feedback.get("actual_impact"):
            metrics["impact_misclassifications"] += 1
        
        # Calculate accuracy
        if metrics["total_feedback"] > 0:
            metrics["overall_accuracy"] = metrics["accurate_predictions"] / metrics["total_feedback"]
            metrics["correction_rate"] = metrics["corrections"] / metrics["total_feedback"]
        
        # Save metrics
        try:
            with open(self.METRICS_FILE, "w") as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            print(f"[WARN] Failed to write metrics: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current feedback metrics.
        
        Returns:
            Dictionary of metrics
        """
        default_metrics = {
            "total_feedback": 0,
            "accurate_predictions": 0,
            "inaccurate_predictions": 0,
            "corrections": 0,
            "severity_misclassifications": 0,
            "impact_misclassifications": 0,
            "overall_accuracy": 0.0,
            "correction_rate": 0.0,
            "last_updated": datetime.utcnow().isoformat(),
        }
        
        if not os.path.exists(self.METRICS_FILE):
            return default_metrics
        
        try:
            with open(self.METRICS_FILE, "r") as f:
                metrics = json.load(f)
                return {**default_metrics, **metrics}
        except Exception as e:
            print(f"[WARN] Failed to read metrics: {e}")
            return default_metrics

    def get_feedback_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve feedback records.
        
        Args:
            limit: Maximum number of records to retrieve
            
        Returns:
            List of feedback records
        """
        records = []
        
        if not os.path.exists(self.FEEDBACK_FILE):
            return records
        
        try:
            with open(self.FEEDBACK_FILE, "r") as f:
                for i, line in enumerate(f):
                    if limit and i >= limit:
                        break
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"[WARN] Failed to read feedback records: {e}")
        
        return records

    def get_feedback_by_incident(self, incident_id: str) -> List[Dict[str, Any]]:
        """Get all feedback for a specific incident.
        
        Args:
            incident_id: Incident ID to query
            
        Returns:
            List of feedback records for this incident
        """
        all_feedback = self.get_feedback_records()
        return [f for f in all_feedback if f["incident_id"] == incident_id]

    def get_false_positives(self) -> List[Dict[str, Any]]:
        """Get incidents that were incorrectly classified as high priority.
        
        Returns:
            List of false positive feedback records
        """
        all_feedback = self.get_feedback_records()
        false_positives = []
        
        for f in all_feedback:
            if f["predicted_severity"] in {"P1", "P2"} and f.get("actual_severity") in {"P3", "P4"}:
                false_positives.append(f)
        
        return false_positives

    def get_false_negatives(self) -> List[Dict[str, Any]]:
        """Get incidents that were incorrectly classified as low priority.
        
        Returns:
            List of false negative feedback records
        """
        all_feedback = self.get_feedback_records()
        false_negatives = []
        
        for f in all_feedback:
            if f["predicted_severity"] in {"P3", "P4"} and f.get("actual_severity") in {"P1", "P2"}:
                false_negatives.append(f)
        
        return false_negatives

    def clear_feedback(self) -> None:
        """Clear all feedback data (for testing)."""
        try:
            if os.path.exists(self.FEEDBACK_FILE):
                os.remove(self.FEEDBACK_FILE)
            if os.path.exists(self.METRICS_FILE):
                os.remove(self.METRICS_FILE)
            print("[INFO] Feedback data cleared.")
        except Exception as e:
            print(f"[WARN] Failed to clear feedback: {e}")


class IncidentFeedbackForm:
    """Interactive feedback form for incident review."""

    def __init__(self, feedback_capture: FeedbackCapture):
        """Initialize feedback form.
        
        Args:
            feedback_capture: FeedbackCapture instance
        """
        self.capture = feedback_capture

    def review_incident(self, incident: IncidentEvent) -> Dict[str, Any]:
        """Generate review form for an incident.
        
        Args:
            incident: IncidentEvent to review
            
        Returns:
            Feedback record
        """
        print("\n=== Incident Review ===")
        print(f"Incident ID: {incident.id}")
        print(f"Predicted Severity: {incident.severity}")
        print(f"Classification: {incident.classification}")
        print(f"Summary: {incident.summary}")
        
        # For CLI, provide simple feedback
        # In production, this could be a web form
        print("\nWas the severity classification accurate? (y/n): ", end="")
        is_accurate = input().strip().lower() == "y"
        
        actual_severity = None
        if not is_accurate:
            print("What should the severity be? (P1/P2/P3/P4): ", end="")
            actual_severity = input().strip().upper()
            if actual_severity not in {"P1", "P2", "P3", "P4"}:
                actual_severity = None
        
        print("Any comments?: ", end="")
        comments = input().strip()
        
        return self.capture.record_feedback(
            incident_id=incident.id,
            predicted_severity=incident.severity,
            actual_severity=actual_severity,
            predicted_impact=incident.classification,
            user_comments=comments,
            is_accurate=is_accurate,
        )
