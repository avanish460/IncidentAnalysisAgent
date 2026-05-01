"""Machine learning-based incident classification engine."""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from .data_models import IncidentEvent, AlertRecord, TicketRecord

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import StandardScaler
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class MLIncidentClassifier:
    """ML-based incident classification using scikit-learn."""

    MODEL_DIR = ".airena2_models"
    SEVERITY_MODEL_PATH = os.path.join(MODEL_DIR, "severity_classifier.pkl")
    IMPACT_MODEL_PATH = os.path.join(MODEL_DIR, "impact_classifier.pkl")
    VECTORIZER_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
    SCALER_PATH = os.path.join(MODEL_DIR, "feature_scaler.pkl")

    def __init__(self):
        """Initialize ML classifier."""
        self.severity_classifier = None
        self.impact_classifier = None
        self.vectorizer = None
        self.scaler = None
        self.ml_enabled = SKLEARN_AVAILABLE
        
        if self.ml_enabled:
            self._ensure_model_dir()
            self._load_or_init_models()

    def _ensure_model_dir(self) -> None:
        """Ensure model directory exists."""
        os.makedirs(self.MODEL_DIR, exist_ok=True)

    def _load_or_init_models(self) -> None:
        """Load pre-trained models or initialize new ones."""
        try:
            if os.path.exists(self.SEVERITY_MODEL_PATH):
                self.severity_classifier = joblib.load(self.SEVERITY_MODEL_PATH)
            else:
                self.severity_classifier = self._init_severity_classifier()
            
            if os.path.exists(self.IMPACT_MODEL_PATH):
                self.impact_classifier = joblib.load(self.IMPACT_MODEL_PATH)
            else:
                self.impact_classifier = self._init_impact_classifier()
            
            if os.path.exists(self.VECTORIZER_PATH):
                self.vectorizer = joblib.load(self.VECTORIZER_PATH)
            else:
                self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
                self._train_vectorizer()
            
            if os.path.exists(self.SCALER_PATH):
                self.scaler = joblib.load(self.SCALER_PATH)
            else:
                self.scaler = StandardScaler()
        except Exception as e:
            print(f"[WARN] Failed to load ML models: {e}")
            self.ml_enabled = False

    def _init_severity_classifier(self) -> Optional[RandomForestClassifier]:
        """Initialize and train severity classifier with default data."""
        if not SKLEARN_AVAILABLE:
            return None
        
        classifier = RandomForestClassifier(n_estimators=10, max_depth=5, random_state=42)
        
        # Train with synthetic patterns
        training_data = self._get_training_severity_data()
        if training_data:
            X, y = training_data
            try:
                classifier.fit(X, y)
                joblib.dump(classifier, self.SEVERITY_MODEL_PATH)
                return classifier
            except Exception as e:
                print(f"[WARN] Failed to train severity classifier: {e}")
        
        return None

    def _init_impact_classifier(self) -> Optional[RandomForestClassifier]:
        """Initialize and train impact classifier with default data."""
        if not SKLEARN_AVAILABLE:
            return None
        
        classifier = RandomForestClassifier(n_estimators=10, max_depth=5, random_state=42)
        
        # Train with synthetic patterns
        training_data = self._get_training_impact_data()
        if training_data:
            X, y = training_data
            try:
                classifier.fit(X, y)
                joblib.dump(classifier, self.IMPACT_MODEL_PATH)
                return classifier
            except Exception as e:
                print(f"[WARN] Failed to train impact classifier: {e}")
        
        return None

    def _train_vectorizer(self) -> None:
        """Train TF-IDF vectorizer with sample text."""
        if not SKLEARN_AVAILABLE:
            return
        
        sample_texts = [
            "CPU usage exceeded threshold",
            "Database connection failures",
            "Request latency spike",
            "Memory utilization critical",
            "Error rate increased",
            "Service timeout",
            "Cluster unavailable",
            "Network latency high",
            "Disk space low",
            "Authentication failed",
        ]
        
        try:
            self.vectorizer.fit(sample_texts)
            joblib.dump(self.vectorizer, self.VECTORIZER_PATH)
        except Exception as e:
            print(f"[WARN] Failed to train vectorizer: {e}")

    def _get_training_severity_data(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Get synthetic training data for severity classification."""
        # Synthetic features: [alert_count, ticket_count, has_critical_keyword, error_rate]
        X = np.array([
            [3, 1, 1, 0.8],   # Critical
            [2, 1, 1, 0.5],   # High
            [1, 0, 0, 0.2],   # Medium
            [1, 0, 0, 0.1],   # Low
            [5, 2, 1, 0.9],   # Critical
            [2, 0, 0, 0.3],   # Medium
        ])
        y = np.array([0, 1, 2, 3, 0, 2])  # 0=P1, 1=P2, 2=P3, 3=P4
        return X, y

    def _get_training_impact_data(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Get synthetic training data for impact classification."""
        # Synthetic features: [severity_score, affected_services, ticket_count]
        X = np.array([
            [1.0, 3, 2],      # Service-impact
            [0.75, 2, 1],     # Service-impact
            [0.5, 1, 0],      # Informational
            [0.25, 0, 0],     # Informational
            [1.0, 4, 3],      # Service-impact
        ])
        y = np.array([0, 0, 1, 1, 0])  # 0=service-impact, 1=informational
        return X, y

    def _extract_features(self, incident: IncidentEvent) -> np.ndarray:
        """Extract features from incident for classification.
        
        Args:
            incident: IncidentEvent to analyze
            
        Returns:
            Feature vector
        """
        alert_count = len(incident.alerts)
        ticket_count = len(incident.tickets)
        
        # Check for critical keywords
        critical_keywords = ["critical", "fatal", "down", "crash", "failed", "error"]
        has_critical = 0
        for alert in incident.alerts:
            if any(kw in alert.message.lower() for kw in critical_keywords):
                has_critical = 1
                break
        
        # Calculate error rate estimate from severity
        severity_scores = {"critical": 0.9, "high": 0.6, "medium": 0.3, "low": 0.1}
        avg_severity = np.mean([
            severity_scores.get(a.severity.lower(), 0.5) for a in incident.alerts
        ]) if incident.alerts else 0.5
        
        features = [
            alert_count,
            ticket_count,
            has_critical,
            avg_severity,
        ]
        
        return np.array([features])

    def classify_severity(self, incident: IncidentEvent) -> str:
        """Classify incident severity using ML model.
        
        Args:
            incident: IncidentEvent to classify
            
        Returns:
            Severity level (P1, P2, P3, P4)
        """
        if not self.ml_enabled or self.severity_classifier is None:
            # Fallback to rule-based
            return self._classify_severity_fallback(incident)
        
        try:
            features = self._extract_features(incident)
            prediction = self.severity_classifier.predict(features)[0]
            severity_map = {0: "P1", 1: "P2", 2: "P3", 3: "P4"}
            return severity_map.get(prediction, "P3")
        except Exception as e:
            print(f"[WARN] ML severity classification failed: {e}")
            return self._classify_severity_fallback(incident)

    def classify_impact(self, incident: IncidentEvent) -> str:
        """Classify incident impact using ML model.
        
        Args:
            incident: IncidentEvent to classify
            
        Returns:
            Impact classification ("service-impact" or "informational")
        """
        if not self.ml_enabled or self.impact_classifier is None:
            # Fallback to rule-based
            return self._classify_impact_fallback(incident)
        
        try:
            severity = self.classify_severity(incident)
            severity_score = {"P1": 1.0, "P2": 0.75, "P3": 0.5, "P4": 0.25}.get(severity, 0.5)
            
            features = np.array([[
                severity_score,
                len(incident.alerts),
                len(incident.tickets),
            ]])
            
            prediction = self.impact_classifier.predict(features)[0]
            impact_map = {0: "service-impact", 1: "informational"}
            return impact_map.get(prediction, "informational")
        except Exception as e:
            print(f"[WARN] ML impact classification failed: {e}")
            return self._classify_impact_fallback(incident)

    def _classify_severity_fallback(self, incident: IncidentEvent) -> str:
        """Rule-based fallback for severity classification."""
        if not incident.alerts:
            return "P4"
        
        has_critical = any(a.severity.lower() == "critical" for a in incident.alerts)
        has_high = any(a.severity.lower() == "high" for a in incident.alerts)
        alert_count = len(incident.alerts)
        
        if has_critical or alert_count >= 5:
            return "P1"
        elif has_high or alert_count >= 3:
            return "P2"
        elif alert_count >= 2:
            return "P3"
        else:
            return "P4"

    def _classify_impact_fallback(self, incident: IncidentEvent) -> str:
        """Rule-based fallback for impact classification."""
        severity = self.classify_severity(incident)
        if severity in {"P1", "P2"}:
            return "service-impact"
        return "informational"

    def retrain_with_feedback(self, feedback_data: List[Dict]) -> None:
        """Retrain models with feedback data.
        
        Args:
            feedback_data: List of feedback entries with corrections
        """
        if not self.ml_enabled:
            return
        
        print(f"[INFO] Retraining models with {len(feedback_data)} feedback entries...")
        # Implementation would involve collecting feedback and retraining
        # This is a placeholder for the feedback loop
        pass
