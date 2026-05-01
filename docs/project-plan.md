# AIrena2.0 Project Plan

## Objective

Create an AI-driven incident and service request analysis assistant that helps operations teams ingest, triage, correlate, analyze, and report on production incidents with greater speed and accuracy.

## Phase 1: Foundation

- Define the core domain models for alerts, tickets, incidents, and service context
- Build a minimal ingestion layer for sample data
- Implement a simple triage workflow for classification and correlation
- Produce a basic incident summary and structured report
- Provide a CLI entrypoint for local experimentation

## Phase 2: Intelligence

- Add machine learning / NLP models for:
  - incident classification and severity prediction
  - alert correlation and grouping
  - root cause hypothesis generation
  - summarization of incident details
- Integrate feedback capture to support continuous learning

## Phase 3: Integration

- Connect to real event sources and ticketing systems
  - monitoring platforms (Prometheus, Datadog, CloudWatch)
  - ticket tools (ServiceNow, Jira)
  - log platforms (ELK, Splunk)
- Add service topology and dependency context
- Build a REST API or web interface for team collaboration

## Phase 4: Validation and rollout

- Define success metrics: MTTD, MTTA, MTTR, precision, recall, routing accuracy
- Evaluate against historic incidents and real tickets
- Iterate based on user feedback and false-positive reduction
- Add guardrails and explainability for human review

## First milestones

1. Create starter repo and project structure
2. Implement `src/airena2/pipeline.py` and `src/airena2/main.py`
3. Add sample data ingestion and processing stubs
4. Validate end-to-end run with synthetic example data
5. Document the architecture and next action plan
