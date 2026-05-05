# Phase 2 Intelligence Features - Quick Reference

## What's New

### 1. Smart Alert Correlation

Your alerts are now intelligently grouped by **semantic meaning**, not just source.

**Example**:

```
Before: "CPU alert on server-1" and "CPU alert on server-2" → 2 groups
After:  "CPU alert on server-1" and "CPU alert on server-2" → 1 group (same issue)
```

**How to use**:

- Automatic in pipeline - no configuration needed
- Configured via `similarity_threshold` parameter (default 0.6)

### 2. ML-Based Severity Classification

Incidents now get classified using machine learning models trained on patterns.

**Features**:

- Automatically predicts severity (P1, P2, P3, P4)
- Learns from your corrections
- Falls back to rules if models unavailable

**Severity Levels**:

- **P1**: Critical - immediate action required
- **P2**: High - escalate to team lead
- **P3**: Medium - review and prioritize
- **P4**: Low - informational only

### 3. Advanced Summarization

Summaries are now generated using AI models for better clarity.

**Example Summary**:

```
CPU usage exceeded 95% in app-server-1 classified as P2 priority.
Detected 5 alert(s) from systems: app-server-1, api-gateway, cache-node-1.
This incident has service-level impact and requires immediate attention.
There are 2 related ticket(s) in the ticketing system.
```

### 4. Feedback & Learning System

Track how accurate our predictions are and help improve them.

**What's Tracked**:

- Correct vs incorrect predictions
- False positives (marked as important but weren't)
- False negatives (missed real issues)
- Overall system accuracy

**View Metrics**:

```python
from airena2.feedback import FeedbackCapture

feedback = FeedbackCapture()
metrics = feedback.get_metrics()
print(f"Overall Accuracy: {metrics['overall_accuracy']:.1%}")
print(f"False Positives: {len(feedback.get_false_positives())}")
print(f"False Negatives: {len(feedback.get_false_negatives())}")
```

### 5. Better RCA (Root Cause Analysis)

Analyzes multiple failure modes and suggests likely causes.

**Example RCA**:

```
Multiple failure modes detected: application errors, resource exhaustion,
connectivity issues. Suggests cascading failure or system overload.
```

## New Module Overview

### `correlation.py`

Semantic alert correlation using spaCy + scikit-learn.

```python
from airena2.correlation import SemanticCorrelationEngine
from airena2.data_models import AlertRecord

correlator = SemanticCorrelationEngine()
groups = correlator.correlate_alerts(alerts, similarity_threshold=0.6)
# Returns: List[List[AlertRecord]] - grouped alerts
```

### `ml_classifier.py`

Machine learning-based incident classification.

```python
from airena2.ml_classifier import MLIncidentClassifier

classifier = MLIncidentClassifier()
severity = classifier.classify_severity(incident)  # Returns "P1", "P2", etc.
impact = classifier.classify_impact(incident)      # Returns "service-impact" or "informational"
```

### `summarization.py`

Advanced incident summarization using transformers.

```python
from airena2.summarization import AdvancedSummarizationEngine

summarizer = AdvancedSummarizationEngine()
brief = summarizer.generate_brief_summary(incident)      # 1-2 sentences
detailed = summarizer.generate_detailed_summary(incident) # 3-5 sentences
key_points = summarizer.extract_key_points(incident)     # List of insights
```

### `feedback.py`

Feedback capture for continuous learning.

```python
from airena2.feedback import FeedbackCapture

feedback = FeedbackCapture()

# Record feedback
feedback.record_feedback(
    incident_id="inc-1",
    predicted_severity="P1",
    actual_severity="P2",  # User's correction
    user_comments="Good but slightly too severe"
)

# Analyze metrics
metrics = feedback.get_metrics()
false_positives = feedback.get_false_positives()
false_negatives = feedback.get_false_negatives()
```

### `analysis.py` (Enhanced)

Now integrates all Phase 2 components with intelligent fallbacks.

```python
from airena2.analysis import AnalysisEngine

engine = AnalysisEngine()

# Multi-level analysis with fallbacks:
# 1. Try LLM (best)
# 2. Try transformers
# 3. Use rules (always works)
summary = engine.summarize_incident(incident)
rca = engine.generate_rca(incident)
recommendations = engine.recommend_actions(incident)

# Record feedback
engine.record_feedback(incident, actual_severity="P2", user_comments="...")
```

## Optional Dependencies

### Auto-Detected & Gracefully Handled

| Dependency   | Feature                | If Missing                        |
| ------------ | ---------------------- | --------------------------------- |
| spacy        | Semantic correlations  | Uses simple embeddings            |
| transformers | Advanced summarization | Uses rule-based summaries         |
| PyTorch      | Transformer backend    | Skips if transformers unavailable |
| scikit-learn | ML classification      | Uses rule-based classification    |

### All optional - system works without them!

## API Endpoints (Phase 3 Preview)

These will be fully implemented in Phase 3:

```bash
# Analyze incident via API
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [...],
    "tickets": [...]
  }'

# Submit feedback
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc-1",
    "predicted_severity": "P1",
    "actual_severity": "P2",
    "comments": "Too severe"
  }'

# Get metrics
curl http://localhost:8000/metrics
```

## Performance Tips

### For Better Correlation

```python
# Install spaCy model for semantic embeddings (better quality)
python -m spacy download en_core_web_sm
```

### For Better Summarization

```python
# Install PyTorch for transformer models (better quality)
pip install torch  # or: conda install pytorch
```

### For Better Classification

```python
# System automatically trains from feedback
# Retrain periodically:
classifier.retrain_with_feedback(feedback.get_feedback_records())
```

## Troubleshooting

### "spaCy model not found"

```bash
python -m spacy download en_core_web_sm
```

System will work with simpler embeddings until you do this.

### "PyTorch not found"

```bash
pip install torch
# or
conda install pytorch
```

System will use rule-based summaries until you do this.

### Models not improving

Feedback must be manually triggered for retraining. More on this in Phase 3.

## What's Different from Phase 1

| Feature         | Phase 1         | Phase 2                         |
| --------------- | --------------- | ------------------------------- |
| Alert Grouping  | By source       | By semantic similarity          |
| Classification  | Rule-based only | ML + rules                      |
| Summarization   | Simple template | AI-generated (LLM/transformers) |
| Learning        | None            | Feedback capture system         |
| RCA             | Basic           | Multi-mode analysis             |
| Recommendations | Generic         | Context-aware suggestions       |
| Reliability     | Limited         | Multi-level fallbacks           |

## Next Steps (Phase 3)

1. ✅ Phase 2: Intelligence (COMPLETE)
2. ✅ Phase 3: Integration (local real-time synthetic connectors complete)
   - Local connector simulation now supports the current integration flow
   - Real external connectors (Prometheus, Datadog, ServiceNow, Jira) will be added later
   - REST API endpoints are available for analysis and simulation
   - Service topology and multi-source correlation are implemented for the local data path
3. ⏳ Phase 4: Validation & Rollout (active next phase)
   - Metrics & success tracking
   - User feedback integration
   - Production hardening

---

**For detailed information**, see [PHASE2_INTELLIGENCE.md](./PHASE2_INTELLIGENCE.md)
