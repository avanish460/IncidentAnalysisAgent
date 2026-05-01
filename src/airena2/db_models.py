"""Database models for persistence layer."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class IncidentRecord(Base):
    """Database model for incidents."""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False, index=True)
    classification = Column(String(100), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    rca = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    impacted_services = Column(JSON, nullable=True)
    alert_count = Column(Integer, default=0)
    ticket_count = Column(Integer, default=0)
    alerts = Column(JSON, nullable=True)
    tickets = Column(JSON, nullable=True)
    custom_metadata = Column(JSON, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "title": self.title,
            "severity": self.severity,
            "classification": self.classification,
            "summary": self.summary,
            "rca": self.rca,
            "recommendations": self.recommendations,
            "impacted_services": self.impacted_services,
            "alert_count": self.alert_count,
            "ticket_count": self.ticket_count,
            "alerts": self.alerts,
            "tickets": self.tickets,
            "metadata": self.custom_metadata,
            "processed_at": self.processed_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


class FeedbackRecord(Base):
    """Database model for feedback entries."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(255), nullable=False, index=True)
    predicted_severity = Column(String(50), nullable=False)
    actual_severity = Column(String(50), nullable=True)
    predicted_impact = Column(String(100), nullable=False)
    actual_impact = Column(String(100), nullable=True)
    user_comments = Column(Text, nullable=True)
    is_accurate = Column(Integer, default=1)
    correction_made = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "predicted_severity": self.predicted_severity,
            "actual_severity": self.actual_severity,
            "predicted_impact": self.predicted_impact,
            "actual_impact": self.actual_impact,
            "user_comments": self.user_comments,
            "is_accurate": bool(self.is_accurate),
            "correction_made": bool(self.correction_made),
            "recorded_at": self.recorded_at.isoformat(),
        }


class AnalyticsRecord(Base):
    """Database model for aggregated metrics."""
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "tags": self.tags,
            "recorded_at": self.recorded_at.isoformat(),
        }
