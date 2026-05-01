from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .connectors import create_connector
from .data_models import AlertRecord, TicketRecord
from .db_service import DatabaseService, FeedbackRepository
from .feedback import FeedbackCapture
from .incident_manager import IncidentStore
from .service_topology import ServiceTopology
from .simulation_controller import SimulationController
from .pipeline import AIPipeline


# API Request/Response Models
class AlertRequest(BaseModel):
    id: str = Field(..., description="Unique alert identifier")
    source: str = Field(..., description="Source system or component")
    severity: str = Field(..., description="Alert severity level")
    message: str = Field(..., description="Alert message/description")
    timestamp: str = Field(..., description="ISO format timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TicketRequest(BaseModel):
    id: str = Field(..., description="Unique ticket identifier")
    system: str = Field(..., description="Ticketing system (e.g., ServiceNow, Jira)")
    category: str = Field(..., description="Ticket category")
    priority: str = Field(..., description="Ticket priority level")
    summary: str = Field(..., description="Ticket summary")
    description: str = Field(..., description="Detailed ticket description")
    created_at: str = Field(..., description="ISO format creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AnalysisRequest(BaseModel):
    alerts: List[AlertRequest] = Field(default_factory=list, description="List of alerts to analyze")
    tickets: List[TicketRequest] = Field(default_factory=list, description="List of tickets to analyze")


class AnalysisResponse(BaseModel):
    incident_id: str = Field(..., description="Generated incident identifier")
    title: str = Field(..., description="Incident title")
    severity: str = Field(..., description="Incident severity")
    classification: str = Field(..., description="Incident classification")
    summary: Optional[str] = Field(None, description="AI-generated incident summary")
    rca: Optional[str] = Field(None, description="Root cause analysis")
    recommendations: Optional[List[str]] = Field(None, description="Actionable recommendations")
    impacted_services: Optional[List[str]] = Field(default_factory=list, description="Services impacted by this incident")
    alert_count: int = Field(..., description="Number of alerts processed")
    ticket_count: int = Field(..., description="Number of tickets processed")
    processed_at: str = Field(..., description="Analysis timestamp")


class IncidentSummaryResponse(BaseModel):
    incident_id: str = Field(..., description="Incident identifier")
    title: str = Field(..., description="Incident title")
    severity: str = Field(..., description="Incident severity")
    classification: str = Field(..., description="Incident classification")
    alert_count: int = Field(..., description="Number of alerts processed")
    ticket_count: int = Field(..., description="Number of tickets processed")
    processed_at: str = Field(..., description="Analysis timestamp")
    impacted_services: Optional[List[str]] = Field(default_factory=list, description="Impacted services")


class ServiceResponse(BaseModel):
    id: str = Field(..., description="Service identifier")
    name: str = Field(..., description="Service name")
    owner: str = Field(..., description="Service owner team")
    criticality: str = Field(..., description="Service criticality")
    description: str = Field(..., description="Service description")
    dependencies: List[str] = Field(default_factory=list, description="Service dependencies")


class FeedbackRequest(BaseModel):
    actual_severity: Optional[str] = Field(None, description="Corrected severity level")
    actual_impact: Optional[str] = Field(None, description="Corrected impact description")
    user_comments: Optional[str] = Field(None, description="User feedback comments")
    is_accurate: bool = Field(..., description="Whether the incident analysis was accurate")


class FeedbackResponse(BaseModel):
    incident_id: str = Field(..., description="Incident identifier")
    recorded: bool = Field(..., description="Whether feedback was recorded successfully")
    details: Optional[str] = Field(None, description="Feedback recording details")


class MetricsResponse(BaseModel):
    total_feedback: int = Field(..., description="Total feedback records")
    accurate_predictions: int = Field(..., description="Number of accurate predictions")
    inaccurate_predictions: int = Field(..., description="Number of inaccurate predictions")
    overall_accuracy: float = Field(..., description="Overall accuracy ratio")
    correction_rate: float = Field(..., description="Correction rate ratio")
    last_updated: str = Field(..., description="Timestamp of last metrics update")


class FetchDataRequest(BaseModel):
    connector: str = Field(default="mock", description="Data connector type")
    scenario: Optional[str] = Field(None, description="Simulation scenario for mock connectors")
    since: Optional[str] = Field(None, description="Fetch data since this datetime (ISO format)")


class FetchDataResponse(BaseModel):
    alerts: List[AlertRequest] = Field(default_factory=list, description="Fetched alerts")
    tickets: List[TicketRequest] = Field(default_factory=list, description="Fetched tickets")
    alert_count: int = Field(..., description="Number of alerts fetched")
    ticket_count: int = Field(..., description="Number of tickets fetched")
    fetched_at: str = Field(..., description="Data fetch timestamp")


class SimulationRequest(BaseModel):
    connector_type: str = Field(default="mock", description="Connector type for simulation")
    scenario: str = Field(default="degradation", description="Simulation scenario (normal, degradation, outage)")
    analyze: bool = Field(default=True, description="Whether to run analysis")
    store_result: bool = Field(default=True, description="Whether to store incident")


class SimulationResponse(BaseModel):
    status: str = Field(..., description="Simulation status")
    reason: Optional[str] = Field(None, description="Failure reason if applicable")
    simulation: Optional[Dict[str, Any]] = Field(None, description="Simulation details")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Analysis result")
    timestamp: str = Field(..., description="Simulation timestamp")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    incident_count: int = Field(..., description="Number of incidents stored")
    timestamp: str = Field(..., description="Health check timestamp")


# FastAPI Application
app = FastAPI(
    title="AIrena2.0 API",
    description="AI-driven incident and service request analysis assistant",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

pipeline = AIPipeline()
incident_store = IncidentStore(use_database=True)
service_topology = ServiceTopology()
feedback_capture = FeedbackCapture()
simulation_controller = SimulationController(pipeline, incident_store, service_topology)


def convert_alert_request_to_record(alert: AlertRequest) -> AlertRecord:
    """Convert API request model to internal data model."""
    return AlertRecord(
        id=alert.id,
        source=alert.source,
        severity=alert.severity,
        message=alert.message,
        timestamp=datetime.fromisoformat(alert.timestamp),
        metadata=alert.metadata
    )


def convert_ticket_request_to_record(ticket: TicketRequest) -> TicketRecord:
    """Convert API request model to internal data model."""
    return TicketRecord(
        id=ticket.id,
        system=ticket.system,
        category=ticket.category,
        priority=ticket.priority,
        summary=ticket.summary,
        description=ticket.description,
        created_at=datetime.fromisoformat(ticket.created_at),
        metadata=ticket.metadata
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_incident(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze alerts and tickets to generate incident insights using AI.

    This endpoint accepts a collection of alerts and tickets, processes them
    through the AI pipeline, and returns structured incident analysis including
    summary, root cause analysis, and actionable recommendations.
    """
    try:
        # Convert request models to internal data models
        alerts = [convert_alert_request_to_record(alert) for alert in request.alerts]
        tickets = [convert_ticket_request_to_record(ticket) for ticket in request.tickets]

        # Convert records to dictionaries for pipeline compatibility
        alert_dicts = [
            {
                "id": alert.id,
                "source": alert.source,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata,
            }
            for alert in alerts
        ]
        ticket_dicts = [
            {
                "id": ticket.id,
                "system": ticket.system,
                "category": ticket.category,
                "priority": ticket.priority,
                "summary": ticket.summary,
                "description": ticket.description,
                "created_at": ticket.created_at.isoformat(),
                "metadata": ticket.metadata,
            }
            for ticket in tickets
        ]

        # Run AI pipeline
        incident = pipeline.run(alert_dicts, ticket_dicts)
        impacted_services = service_topology.analyze_impacted_services(incident.alerts)
        incident.metadata["impacted_services"] = impacted_services
        incident_store.add_incident(
            incident,
            processed_at=datetime.utcnow().isoformat(),
            impacted_services=impacted_services,
        )

        # Convert to response model
        return AnalysisResponse(
            incident_id=incident.id,
            title=incident.title,
            severity=incident.severity,
            classification=incident.classification,
            summary=incident.summary,
            rca=incident.rca,
            recommendations=incident.recommendations,
            impacted_services=impacted_services,
            alert_count=len(alerts),
            ticket_count=len(tickets),
            processed_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/fetch", response_model=FetchDataResponse)
async def fetch_data(request: FetchDataRequest) -> FetchDataResponse:
    """
    Fetch alerts and tickets from external data connectors.

    This endpoint connects to external systems (ServiceNow, etc.) to fetch
    real incident data for analysis.
    """
    try:
        since = None
        if request.since:
            try:
                since = datetime.fromisoformat(request.since)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid datetime format: {request.since}")

        connector = create_connector(request.connector, scenario=request.scenario or "degradation")

        if not connector.test_connection():
            raise HTTPException(status_code=503, detail=f"Cannot connect to {request.connector} data source")

        alerts = connector.fetch_alerts(since)
        tickets = connector.fetch_tickets(since)

        # Convert to response format
        alert_responses = [
            AlertRequest(
                id=alert["id"],
                source=alert["source"],
                severity=alert["severity"],
                message=alert["message"],
                timestamp=alert["timestamp"],
                metadata=alert["metadata"]
            )
            for alert in alerts
        ]

        ticket_responses = [
            TicketRequest(
                id=ticket["id"],
                system=ticket["system"],
                category=ticket["category"],
                priority=ticket["priority"],
                summary=ticket["summary"],
                description=ticket["description"],
                created_at=ticket["created_at"],
                metadata=ticket["metadata"]
            )
            for ticket in tickets
        ]

        return FetchDataResponse(
            alerts=alert_responses,
            tickets=ticket_responses,
            alert_count=len(alerts),
            ticket_count=len(tickets),
            fetched_at=datetime.utcnow().isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetch failed: {str(e)}")


@app.get("/incidents", response_model=List[IncidentSummaryResponse])
async def list_incidents(severity: Optional[str] = None, classification: Optional[str] = None) -> List[IncidentSummaryResponse]:
    """List stored incident summaries."""
    incidents = incident_store.list_incidents(severity=severity, classification=classification)
    return [
        IncidentSummaryResponse(
            incident_id=item["incident_id"],
            title=item["title"],
            severity=item["severity"],
            classification=item["classification"],
            alert_count=item["alert_count"],
            ticket_count=item["ticket_count"],
            processed_at=item["processed_at"],
            impacted_services=item.get("impacted_services", []),
        )
        for item in incidents
    ]


@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str) -> Dict[str, Any]:
    """Retrieve a detailed stored incident."""
    incident = incident_store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.post("/incidents/{incident_id}/feedback", response_model=FeedbackResponse)
async def submit_incident_feedback(incident_id: str, feedback: FeedbackRequest) -> FeedbackResponse:
    """Capture feedback for a stored incident."""
    stored_incident = incident_store.get_incident(incident_id)
    if not stored_incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    feedback_record = feedback_capture.record_feedback(
        incident_id=incident_id,
        predicted_severity=stored_incident.get("severity", "unknown"),
        actual_severity=feedback.actual_severity,
        predicted_impact=stored_incident.get("classification", "informational"),
        actual_impact=feedback.actual_impact,
        user_comments=feedback.user_comments or "",
        is_accurate=feedback.is_accurate,
    )

    return FeedbackResponse(
        incident_id=incident_id,
        recorded=True,
        details=f"Feedback recorded at {feedback_record['timestamp']}"
    )


@app.get("/services", response_model=List[ServiceResponse])
async def list_services() -> List[ServiceResponse]:
    """List service topology definitions."""
    return [
        ServiceResponse(
            id=svc.id,
            name=svc.name,
            owner=svc.owner,
            criticality=svc.criticality,
            description=svc.description,
            dependencies=svc.dependencies,
        )
        for svc in service_topology.get_all_services()
    ]


@app.get("/metrics", response_model=MetricsResponse)
async def metrics() -> MetricsResponse:
    """Retrieve feedback metrics."""
    metrics = feedback_capture.get_metrics()
    return MetricsResponse(
        total_feedback=metrics.get("total_feedback", 0),
        accurate_predictions=metrics.get("accurate_predictions", 0),
        inaccurate_predictions=metrics.get("inaccurate_predictions", 0),
        overall_accuracy=metrics.get("overall_accuracy", 0.0),
        correction_rate=metrics.get("correction_rate", 0.0),
        last_updated=metrics.get("last_updated", datetime.utcnow().isoformat()),
    )


@app.post("/simulate", response_model=SimulationResponse)
async def simulate_incident(request: SimulationRequest) -> SimulationResponse:
    """Run a Phase 3 simulation end-to-end.
    
    This endpoint orchestrates the full Phase 3 pipeline:
    1. Generates simulated data from a connector
    2. Analyzes the data through the AI pipeline
    3. Detects impacted services
    4. Stores the incident
    5. Returns complete results
    """
    result = simulation_controller.run_simulation(
        connector_type=request.connector_type,
        scenario=request.scenario,
        analyze=request.analyze,
        store_result=request.store_result,
    )
    
    return SimulationResponse(
        status=result.get("status", "failed"),
        reason=result.get("reason"),
        simulation=result.get("simulation"),
        analysis=result.get("analysis"),
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        version="0.1.0",
        incident_count=incident_store.count(),
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AIrena2.0 API - AI-driven incident analysis",
        "docs": "/docs",
        "health": "/health"
    }