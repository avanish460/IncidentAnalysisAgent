"""Semantic alert correlation engine for intelligent alert grouping."""

from __future__ import annotations

from typing import List, Tuple
import numpy as np

from .data_models import AlertRecord

try:
    import spacy
    from sklearn.metrics.pairwise import cosine_similarity
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class SemanticCorrelationEngine:
    """Advanced alert correlation using semantic similarity."""

    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize correlation engine with spaCy model.
        
        Args:
            model_name: spaCy model to use (default: en_core_web_sm)
        """
        self.nlp = None
        self.model_name = model_name
        
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(model_name)
            except OSError:
                print(f"[WARN] spaCy model '{model_name}' not found. Falling back to basic correlation.")
                self.nlp = None

    def _get_alert_embedding(self, alert: AlertRecord) -> np.ndarray:
        """Generate semantic embedding for an alert.
        
        Args:
            alert: AlertRecord to embed
            
        Returns:
            numpy array of embedding vector
        """
        if self.nlp is None:
            # Fallback: simple feature vector
            return self._simple_embedding(alert)
        
        # Use spaCy to create embeddings from alert message
        doc = self.nlp(alert.message)
        
        # Combine message vector with severity metadata
        severity_map = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
        severity_score = severity_map.get(alert.severity.lower(), 0.5)
        
        # Create combined embedding
        embedding = doc.vector.copy()
        if embedding.size == 0:
            embedding = np.zeros(96)  # spaCy default
        
        # Add severity as a feature
        embedding = np.append(embedding, [severity_score])
        
        return embedding

    def _simple_embedding(self, alert: AlertRecord) -> np.ndarray:
        """Simple embedding fallback when spaCy is not available.
        
        Args:
            alert: AlertRecord to embed
            
        Returns:
            Simple feature vector based on alert properties
        """
        # Basic feature extraction
        severity_map = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
        severity_score = severity_map.get(alert.severity.lower(), 0.5)
        
        # Message length and keyword features
        message_lower = alert.message.lower()
        features = [
            severity_score,
            len(alert.message) / 100.0,  # Normalized message length
            1.0 if "error" in message_lower else 0.0,
            1.0 if "timeout" in message_lower else 0.0,
            1.0 if "cpu" in message_lower else 0.0,
            1.0 if "memory" in message_lower else 0.0,
            1.0 if "disk" in message_lower else 0.0,
            1.0 if "database" in message_lower else 0.0,
            1.0 if "connection" in message_lower else 0.0,
            1.0 if "failed" in message_lower else 0.0,
        ]
        
        return np.array(features)

    def correlate_alerts(
        self, 
        alerts: List[AlertRecord], 
        similarity_threshold: float = 0.6
    ) -> List[List[AlertRecord]]:
        """Group alerts based on semantic similarity.
        
        Args:
            alerts: List of alerts to correlate
            similarity_threshold: Minimum similarity score to group alerts (0.0-1.0)
            
        Returns:
            List of alert groups (each group is a list of related alerts)
        """
        if not alerts:
            return []
        
        if len(alerts) == 1:
            return [[alerts[0]]]
        
        # Generate embeddings for all alerts
        embeddings = np.array([self._get_alert_embedding(alert) for alert in alerts])
        
        # Compute pairwise similarities
        similarities = cosine_similarity(embeddings)
        
        # Greedy clustering based on similarity threshold
        groups: List[List[AlertRecord]] = []
        assigned = set()
        
        for i, alert in enumerate(alerts):
            if i in assigned:
                continue
            
            # Start a new group with this alert
            group = [alert]
            assigned.add(i)
            
            # Find all alerts similar to this one
            for j in range(i + 1, len(alerts)):
                if j not in assigned and similarities[i][j] >= similarity_threshold:
                    group.append(alerts[j])
                    assigned.add(j)
            
            groups.append(group)
        
        return groups

    def get_alert_similarity(self, alert1: AlertRecord, alert2: AlertRecord) -> float:
        """Calculate similarity score between two alerts.
        
        Args:
            alert1: First alert
            alert2: Second alert
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        emb1 = self._get_alert_embedding(alert1)
        emb2 = self._get_alert_embedding(alert2)
        
        # Reshape for similarity calculation
        emb1 = emb1.reshape(1, -1)
        emb2 = emb2.reshape(1, -1)
        
        similarity = cosine_similarity(emb1, emb2)[0][0]
        return max(0.0, min(1.0, float(similarity)))  # Clamp to [0, 1]
