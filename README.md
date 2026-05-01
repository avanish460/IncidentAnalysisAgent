# AIrena2.0

AIrena2.0 is an one month hackathon where I have to build AI-driven incident and service request analysis assistant designed to ingest alerts, logs, tickets, and operational context, then produce faster triage, correlation, root-cause analysis, and report generation.

## Vision

- Reduce alert noise and surface high-value incidents
- Correlate related events into a single incident view
- Classify and route requests with accuracy
- Generate concise incident summaries and RCA hypotheses
- Provide a modular, extensible AI pipeline for operations teams

## Starter architecture

- `src/airena2/data_models.py`: domain model definitions
- `src/airena2/data_ingest.py`: ingestion and normalization of sources
- `src/airena2/triage.py`: incident classification and alert correlation
- `src/airena2/analysis.py`: root-cause analysis and summarization
- `src/airena2/reporting.py`: report generation and output formatting
- `src/airena2/pipeline.py`: orchestrates the end-to-end workflow
- `src/airena2/main.py`: CLI entrypoint for local execution

## Project plan

See `docs/project-plan.md` for the phased roadmap and next milestones.

## Quick start

1. Create a Python environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install -e .
   ```
2. Set up your OpenAI API key and endpoint:

   ```powershell
   # Copy the example file
   Copy-Item .env.example .env

   # Edit .env and add your actual API key and API base URL
   notepad .env
   ```

   In `.env`, set:
   ```text
   OPENAI_API_KEY=your-actual-api-key-here
   OPENAI_API_BASE=https://aicafe.hcl.com/AICafeService/api/v1/subscription/openai/deployments/gpt-4.1
   OPENAI_API_VERSION=2024-12-01-preview
   OPENAI_MODEL=gpt-4.1
   ```

3. Run the starter pipeline with sample data:
   ```powershell
   python -m airena2.main --sample
   ```
4. Generate synthetic dummy data to test/train the pipeline:
   ```powershell
   python -m airena2.main --dummy --alerts 12 --tickets 4
   ```

If `OPENAI_API_KEY` is present in your `.env` file, the pipeline will use OpenAI GPT-4 to build richer incident summaries, RCA, and recommendations.

## Data Connectors

AIrena2.0 supports connecting to external data sources for real incident data:

### Supported Connectors

- **ServiceNow**: Enterprise ITSM platform integration
- **Mock**: Test connector with sample data (default)

### CLI Usage with Connectors

```powershell
# Use mock data (default)
python -m airena2.main

# Fetch from ServiceNow (requires environment variables)
$env:SERVICENOW_INSTANCE_URL = "https://yourinstance.servicenow.com"
$env:SERVICENOW_USERNAME = "your-username"
$env:SERVICENOW_PASSWORD = "your-password"
python -m airena2.main --connector servicenow

# Fetch recent data (last 24 hours)
python -m airena2.main --connector servicenow --since "2024-01-14T10:00:00"
```

### API Endpoints for Connectors

**`POST /fetch`** - Fetch data from external connectors
```json
{
  "connector": "servicenow",
  "since": "2024-01-14T10:00:00"
}
```

**Response:**
```json
{
  "alerts": [...],
  "tickets": [...],
  "alert_count": 5,
  "ticket_count": 12,
  "fetched_at": "2024-01-15T10:35:00Z"
}
```

### ServiceNow Setup

1. Get your ServiceNow instance URL
2. Create a user with incident read permissions
3. Set environment variables:
   ```powershell
   $env:SERVICENOW_INSTANCE_URL = "https://yourinstance.servicenow.com"
   $env:SERVICENOW_USERNAME = "integration-user"
   $env:SERVICENOW_PASSWORD = "secure-password"
   ```

## API Usage

AIrena2.0 includes a REST API for programmatic access to incident analysis.

### Start the API Server

```powershell
python -m airena2.main --api
```

The server will start on `http://localhost:8000` with interactive API documentation at `http://localhost:8000/docs`.

### API Endpoints

- `GET /` - API information and links
- `GET /health` - Service health check
- `POST /analyze` - Analyze alerts and tickets

### Example API Request

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [
      {
        "id": "A-1001",
        "source": "app-server-1",
        "severity": "critical",
        "message": "CPU usage exceeded 95%",
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {"service": "payments"}
      }
    ],
    "tickets": [
      {
        "id": "T-2001",
        "system": "ServiceNow",
        "category": "incident",
        "priority": "high",
        "summary": "Production payment service is degraded",
        "description": "Payments are timing out for customers and monitoring alerts show sustained high CPU.",
        "created_at": "2024-01-15T10:25:00Z",
        "metadata": {"assignee": "ops-team"}
      }
    ]
  }'
```

### Example API Response

```json
{
  "incident_id": "incident-A-ABC123",
  "title": "Payment Service Degradation",
  "severity": "P1",
  "classification": "service-impact",
  "summary": "Critical incident affecting payment processing with high CPU usage...",
  "rca": "Root cause appears to be resource exhaustion on app-server-1...",
  "recommendations": [
    "Scale up application servers",
    "Investigate recent code deployments",
    "Enable auto-scaling policies"
  ],
  "alert_count": 1,
  "ticket_count": 1,
  "processed_at": "2024-01-15T10:35:00Z"
}
```

## Goals for the first iteration

- ingest sample alerts, tickets, and log metadata
- classify incident severity and type
- correlate related alerts
- generate a basic narrative summary
- capture feedback and store results for future training
