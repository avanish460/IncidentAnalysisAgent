"""Database service for managing persistence."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from .db_models import Base, IncidentRecord, FeedbackRecord, AnalyticsRecord


class DatabaseService:
    """Manages database connections and operations."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        """Initialize database service.
        
        Args:
            database_url: SQLAlchemy database URL. If None, uses SQLite in .airena2_db directory.
        """
        if database_url is None:
            db_dir = ".airena2_db"
            os.makedirs(db_dir, exist_ok=True)
            database_url = f"sqlite:///{os.path.join(db_dir, 'airena2.db')}"
        
        self.database_url = database_url
        connect_args = {}
        if database_url.startswith("sqlite"):
            # Avoid keeping SQLite connections bound across threads and help test DB file cleanup.
            connect_args = {"check_same_thread": False}

        # Prevent persistent connections that can keep the SQLite file locked on Windows.
        self.engine = create_engine(
            database_url,
            echo=False,
            poolclass=NullPool,
            connect_args=connect_args,
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def initialize_db(self) -> None:
        """Create database tables."""
        Base.metadata.create_all(self.engine)
        
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def close(self) -> None:
        """Close database connection."""
        self.engine.dispose()


class IncidentRepository:
    """Repository for incident data access."""
    
    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize repository.
        
        Args:
            db_service: DatabaseService instance
        """
        self.db_service = db_service
    
    def create_incident(
        self,
        incident_id: str,
        title: str,
        severity: str,
        classification: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new incident record.
        
        Args:
            incident_id: Unique incident identifier
            title: Incident title
            severity: Severity level
            classification: Incident classification
            **kwargs: Additional fields
            
        Returns:
            Created incident record as dict
        """
        from datetime import datetime
        
        session = self.db_service.get_session()
        try:
            # Convert processed_at to datetime if it's a string
            processed_at = kwargs.get("processed_at")
            if isinstance(processed_at, str):
                try:
                    processed_at = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
                except ValueError:
                    processed_at = datetime.utcnow()
            elif processed_at is None:
                processed_at = datetime.utcnow()
            
            existing = session.query(IncidentRecord).filter(
                IncidentRecord.incident_id == incident_id
            ).first()

            if existing is not None:
                # Upsert behavior to avoid UNIQUE constraint failures across test runs
                existing.title = title
                existing.severity = severity
                existing.classification = classification
                existing.summary = kwargs.get("summary")
                existing.rca = kwargs.get("rca")
                existing.recommendations = kwargs.get("recommendations")
                existing.impacted_services = kwargs.get("impacted_services")
                existing.alert_count = kwargs.get("alert_count", 0)
                existing.ticket_count = kwargs.get("ticket_count", 0)
                existing.alerts = kwargs.get("alerts")
                existing.tickets = kwargs.get("tickets")
                existing.custom_metadata = kwargs.get("metadata")
                existing.processed_at = processed_at
                session.commit()
                return existing.to_dict()

            record = IncidentRecord(
                incident_id=incident_id,
                title=title,
                severity=severity,
                classification=classification,
                summary=kwargs.get("summary"),
                rca=kwargs.get("rca"),
                recommendations=kwargs.get("recommendations"),
                impacted_services=kwargs.get("impacted_services"),
                alert_count=kwargs.get("alert_count", 0),
                ticket_count=kwargs.get("ticket_count", 0),
                alerts=kwargs.get("alerts"),
                tickets=kwargs.get("tickets"),
                custom_metadata=kwargs.get("metadata"),
                processed_at=processed_at,
            )
            session.add(record)
            session.commit()
            return record.to_dict()
        finally:
            session.close()
    
    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an incident by ID.
        
        Args:
            incident_id: Incident identifier
            
        Returns:
            Incident record as dict or None if not found
        """
        session = self.db_service.get_session()
        try:
            record = session.query(IncidentRecord).filter(
                IncidentRecord.incident_id == incident_id
            ).first()
            return record.to_dict() if record else None
        finally:
            session.close()
    
    def list_incidents(
        self,
        severity: Optional[str] = None,
        classification: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List incidents with optional filtering.
        
        Args:
            severity: Filter by severity
            classification: Filter by classification
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of incident records as dicts
        """
        session = self.db_service.get_session()
        try:
            query = session.query(IncidentRecord)
            
            if severity:
                query = query.filter(IncidentRecord.severity == severity)
            if classification:
                query = query.filter(IncidentRecord.classification == classification)
            
            records = query.order_by(
                desc(IncidentRecord.processed_at)
            ).limit(limit).offset(offset).all()
            
            return [record.to_dict() for record in records]
        finally:
            session.close()
    
    def update_incident(
        self,
        incident_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update an incident record.
        
        Args:
            incident_id: Incident identifier
            **kwargs: Fields to update
            
        Returns:
            Updated incident record as dict or None if not found
        """
        session = self.db_service.get_session()
        try:
            record = session.query(IncidentRecord).filter(
                IncidentRecord.incident_id == incident_id
            ).first()
            
            if not record:
                return None
            
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            session.commit()
            return record.to_dict()
        finally:
            session.close()
    
    def delete_incident(self, incident_id: str) -> bool:
        """Delete an incident record.
        
        Args:
            incident_id: Incident identifier
            
        Returns:
            True if deleted, False if not found
        """
        session = self.db_service.get_session()
        try:
            record = session.query(IncidentRecord).filter(
                IncidentRecord.incident_id == incident_id
            ).first()
            
            if not record:
                return False
            
            session.delete(record)
            session.commit()
            return True
        finally:
            session.close()
    
    def count_incidents(self) -> int:
        """Get total incident count.
        
        Returns:
            Total number of incidents
        """
        session = self.db_service.get_session()
        try:
            return session.query(IncidentRecord).count()
        finally:
            session.close()


class FeedbackRepository:
    """Repository for feedback data access."""
    
    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize repository.
        
        Args:
            db_service: DatabaseService instance
        """
        self.db_service = db_service
    
    def create_feedback(
        self,
        incident_id: str,
        predicted_severity: str,
        predicted_impact: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new feedback record.
        
        Args:
            incident_id: Related incident ID
            predicted_severity: Model's prediction
            predicted_impact: Model's impact prediction
            **kwargs: Additional fields
            
        Returns:
            Created feedback record as dict
        """
        session = self.db_service.get_session()
        try:
            record = FeedbackRecord(
                incident_id=incident_id,
                predicted_severity=predicted_severity,
                actual_severity=kwargs.get("actual_severity"),
                predicted_impact=predicted_impact,
                actual_impact=kwargs.get("actual_impact"),
                user_comments=kwargs.get("user_comments"),
                is_accurate=1 if kwargs.get("is_accurate", True) else 0,
                correction_made=1 if kwargs.get("correction_made", False) else 0,
            )
            session.add(record)
            session.commit()
            return record.to_dict()
        finally:
            session.close()
    
    def list_feedback(
        self,
        incident_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List feedback records with optional filtering.
        
        Args:
            incident_id: Filter by incident ID
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of feedback records as dicts
        """
        session = self.db_service.get_session()
        try:
            query = session.query(FeedbackRecord)
            
            if incident_id:
                query = query.filter(FeedbackRecord.incident_id == incident_id)
            
            records = query.order_by(
                desc(FeedbackRecord.recorded_at)
            ).limit(limit).offset(offset).all()
            
            return [record.to_dict() for record in records]
        finally:
            session.close()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Calculate feedback metrics.
        
        Returns:
            Dictionary of metrics
        """
        session = self.db_service.get_session()
        try:
            total = session.query(FeedbackRecord).count()
            accurate = session.query(FeedbackRecord).filter(
                FeedbackRecord.is_accurate == 1
            ).count()
            corrections = session.query(FeedbackRecord).filter(
                FeedbackRecord.correction_made == 1
            ).count()
            
            accuracy = (accurate / total * 100) if total > 0 else 0.0
            correction_rate = (corrections / total * 100) if total > 0 else 0.0
            
            return {
                "total_feedback": total,
                "accurate_predictions": accurate,
                "inaccurate_predictions": total - accurate,
                "overall_accuracy": accuracy,
                "correction_rate": correction_rate,
            }
        finally:
            session.close()


class AnalyticsRepository:
    """Repository for analytics data access."""
    
    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize repository.
        
        Args:
            db_service: DatabaseService instance
        """
        self.db_service = db_service
    
    def record_metric(
        self,
        metric_name: str,
        metric_value: str,
        tags: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a metric.
        
        Args:
            metric_name: Name of the metric
            metric_value: Value of the metric
            tags: Optional tags for categorization
            
        Returns:
            Created metric record as dict
        """
        session = self.db_service.get_session()
        try:
            record = AnalyticsRecord(
                metric_name=metric_name,
                metric_value=metric_value,
                tags=tags,
            )
            session.add(record)
            session.commit()
            return record.to_dict()
        finally:
            session.close()
    
    def query_metrics(
        self,
        metric_name: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Query metrics.
        
        Args:
            metric_name: Filter by metric name
            limit: Maximum number of records
            
        Returns:
            List of metric records as dicts
        """
        session = self.db_service.get_session()
        try:
            query = session.query(AnalyticsRecord)
            
            if metric_name:
                query = query.filter(AnalyticsRecord.metric_name == metric_name)
            
            records = query.order_by(
                desc(AnalyticsRecord.recorded_at)
            ).limit(limit).all()
            
            return [record.to_dict() for record in records]
        finally:
            session.close()
