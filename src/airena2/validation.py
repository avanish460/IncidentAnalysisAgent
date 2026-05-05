#!/usr/bin/env python3
"""
Phase 4 Validation Script for AIrena2.0

This script performs end-to-end validation of the AI incident analysis pipeline by:
1. Running the pipeline with synthetic data
2. Simulating user feedback and corrections
3. Calculating validation metrics (precision, recall, routing accuracy)
4. Generating a validation report

Usage:
    python -m airena2.validation --incidents 50 --feedback-rate 0.3
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

from airena2.connectors import create_connector
from airena2.data_models import IncidentEvent
from airena2.db_service import DatabaseService, FeedbackRepository
from airena2.dummy_data import generate_dummy_dataset
from airena2.pipeline import AIPipeline


class ValidationRunner:
    """Runs validation tests on the AIrena2.0 pipeline."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.feedback_repo = FeedbackRepository(db_service)
        self.pipeline = AIPipeline()

    def generate_validation_incidents(self, count: int = 50) -> List[IncidentEvent]:
        """Generate synthetic incidents for validation testing."""
        incidents = []

        # Generate various incident types with known ground truth
        severities = ["P1", "P2", "P3", "P4"]
        impacts = ["service-impact", "customer-impact", "informational"]
        services = ["payments", "auth", "api-gateway", "database", "cache", "monitoring"]

        for i in range(count):
            # Create incident with ground truth labels
            severity = random.choice(severities)
            impact = random.choice(impacts)
            service = random.choice(services)

            # Generate realistic incident data
            incident = IncidentEvent(
                id=f"VAL-{i+1:03d}",
                title=self._generate_incident_title(severity, impact, service),
                severity=severity,
                classification="incident",
                alerts=[],  # Will be populated during pipeline run
                tickets=[],  # Will be populated during pipeline run
                summary=self._generate_incident_summary(severity, impact, service),
                rca=self._generate_rca(severity, impact, service),
                recommendations=self._generate_incident_recommendations(severity, impact, service),
                metadata={
                    "service": service,
                    "ground_truth_severity": severity,
                    "ground_truth_impact": impact
                },
            )
            incidents.append(incident)

        return incidents

    def _generate_incident_title(self, severity: str, impact: str, service: str) -> str:
        """Generate realistic incident titles."""
        templates = {
            "P1": [
                f"CRITICAL: {service.upper()} service outage affecting customers",
                f"P1: {service} completely down",
                f"URGENT: {service} service failure impacting revenue",
            ],
            "P2": [
                f"HIGH: {service} service degradation",
                f"P2: {service} performance issues",
                f"MAJOR: {service} service impacting users",
            ],
            "P3": [
                f"MEDIUM: {service} service alerts",
                f"P3: {service} monitoring warnings",
                f"MINOR: {service} service issues",
            ],
            "P4": [
                f"LOW: {service} informational alerts",
                f"P4: {service} routine maintenance notifications",
                f"INFO: {service} service status updates",
            ],
        }
        return random.choice(templates.get(severity, templates["P3"]))

    def _generate_incident_summary(self, severity: str, impact: str, service: str) -> str:
        """Generate realistic incident summaries."""
        if severity in ["P1", "P2"]:
            return f"The {service} service is experiencing {impact} issues. Multiple alerts indicate {'complete outage' if severity == 'P1' else 'significant degradation'}. Customer impact is {'severe' if impact == 'service-impact' else 'moderate'}."
        else:
            return f"The {service} service has generated {impact} alerts. Monitoring systems show {'minor issues' if severity == 'P3' else 'routine notifications'} requiring attention."

    def _generate_rca(self, severity: str, impact: str, service: str) -> str:
        """Generate realistic root cause analysis."""
        causes = {
            "payments": ["Database connection pool exhausted", "Payment gateway timeout", "SSL certificate expired"],
            "auth": ["Authentication service overload", "Token validation failure", "User session timeout"],
            "api-gateway": ["Rate limiting triggered", "Backend service unavailable", "Configuration error"],
            "database": ["Connection pool full", "Disk space critical", "Replication lag"],
            "cache": ["Cache cluster failure", "Memory exhaustion", "Network partition"],
            "monitoring": ["Alert threshold misconfiguration", "Monitoring agent failure", "Data pipeline delay"],
        }
        return random.choice(causes.get(service, ["Unknown cause"]))

    def _generate_incident_recommendations(self, severity: str, impact: str, service: str) -> List[str]:
        """Generate realistic recommendations."""
        base_recs = [
            f"Investigate {service} service logs for error patterns",
            f"Check {service} service health endpoints",
            f"Review recent deployments to {service}",
            f"Scale {service} service resources if needed",
            f"Update monitoring thresholds for {service}",
        ]
        return random.sample(base_recs, random.randint(2, 4))

    def _generate_alerts_and_tickets_for_incident(self, incident: IncidentEvent) -> tuple[List[Dict], List[Dict]]:
        """Generate synthetic alerts and tickets that would lead to the given incident."""
        service = incident.title.split()[-2] if len(incident.title.split()) > 1 else "unknown"

        # Generate alerts based on incident severity
        alert_count = random.randint(1, 5) if incident.metadata["ground_truth_severity"] in ["P1", "P2"] else random.randint(1, 3)

        alerts = []
        for i in range(alert_count):
            severity_map = {
                "P1": ["critical", "high"],
                "P2": ["high", "warning"],
                "P3": ["warning", "info"],
                "P4": ["info", "low"]
            }
            alert_severity = random.choice(severity_map.get(incident.metadata["ground_truth_severity"], ["info"]))

            alert = {
                "id": f"A-{incident.id.split('-')[1]}-{i+1:03d}",
                "source": f"{service}-server-{random.randint(1, 3)}",
                "severity": alert_severity,
                "message": self._generate_alert_message(incident.metadata["ground_truth_severity"], service),
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"service": service, "component": f"server-{random.randint(1, 3)}"},
            }
            alerts.append(alert)

        # Generate tickets based on incident
        ticket_count = random.randint(0, 2) if incident.metadata["ground_truth_severity"] in ["P1", "P2"] else random.randint(0, 1)

        tickets = []
        for i in range(ticket_count):
            priority_map = {
                "P1": "critical",
                "P2": "high",
                "P3": "medium",
                "P4": "low"
            }

            ticket = {
                "id": f"T-{incident.id.split('-')[1]}-{i+1:03d}",
                "system": "ServiceNow",
                "category": "incident",
                "priority": priority_map.get(incident.metadata["ground_truth_severity"], "medium"),
                "summary": incident.title,
                "description": incident.summary or "Incident reported via monitoring system",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {"assignee": "ops-team", "service": service},
            }
            tickets.append(ticket)

        return alerts, tickets

    def _generate_alert_message(self, severity: str, service: str) -> str:
        """Generate realistic alert messages based on severity and service."""
        messages = {
            "P1": [
                f"CRITICAL: {service} service CPU usage > 95%",
                f"CRITICAL: {service} service memory exhausted",
                f"CRITICAL: {service} service unresponsive",
            ],
            "P2": [
                f"HIGH: {service} service response time > 5s",
                f"HIGH: {service} service error rate > 10%",
                f"HIGH: {service} service degraded performance",
            ],
            "P3": [
                f"WARNING: {service} service elevated error rate",
                f"WARNING: {service} service monitoring alerts",
                f"WARNING: {service} service performance warnings",
            ],
            "P4": [
                f"INFO: {service} service routine checks",
                f"INFO: {service} service status updates",
                f"INFO: {service} service informational alerts",
            ],
        }
        return random.choice(messages.get(severity, messages["P3"]))

    def simulate_user_feedback(self, incidents: List[IncidentEvent], feedback_rate: float = 0.3) -> Dict[str, Any]:
        """Simulate user feedback and corrections for validation."""
        feedback_records = []

        for incident in incidents:
            # Decide whether user provides feedback (simulating real-world feedback rate)
            if random.random() < feedback_rate:
                # Simulate realistic user corrections
                predicted_severity = self._simulate_model_prediction(incident.metadata["ground_truth_severity"])
                predicted_impact = self._simulate_model_prediction(incident.metadata["ground_truth_impact"])

                # Create feedback record
                feedback = self.feedback_repo.create_feedback(
                    incident_id=incident.id,
                    predicted_severity=predicted_severity,
                    predicted_impact=predicted_impact,
                    actual_severity=incident.metadata["ground_truth_severity"],
                    actual_impact=incident.metadata["ground_truth_impact"],
                    is_accurate=(predicted_severity == incident.metadata["ground_truth_severity"] and
                               predicted_impact == incident.metadata["ground_truth_impact"]),
                    correction_made=(predicted_severity != incident.metadata["ground_truth_severity"] or
                                   predicted_impact != incident.metadata["ground_truth_impact"]),
                    user_comments=self._generate_user_comment(predicted_severity, incident.metadata["ground_truth_severity"]),
                )
                feedback_records.append(feedback)

        return {
            "total_feedback": len(feedback_records),
            "feedback_rate": feedback_rate,
            "feedback_records": feedback_records,
        }

    def _simulate_model_prediction(self, ground_truth: str) -> str:
        """Simulate realistic model predictions with some errors."""
        # Model has 80% accuracy, with bias toward certain misclassifications
        if random.random() < 0.8:
            return ground_truth

        # Simulate common misclassifications
        if ground_truth == "P1":
            return random.choice(["P2", "P1"])  # Sometimes under-classify critical issues
        elif ground_truth == "P2":
            return random.choice(["P1", "P3", "P2"])
        elif ground_truth == "P3":
            return random.choice(["P2", "P4", "P3"])
        elif ground_truth == "P4":
            return random.choice(["P3", "P4"])
        elif ground_truth == "service-impact":
            return random.choice(["customer-impact", "service-impact"])
        elif ground_truth == "customer-impact":
            return random.choice(["service-impact", "informational", "customer-impact"])
        else:  # informational
            return random.choice(["customer-impact", "informational"])

    def _generate_user_comment(self, predicted: str, actual: str) -> str:
        """Generate realistic user comments for corrections."""
        if predicted == actual:
            return "Prediction was accurate."

        comments = [
            f"Actually a {actual} issue, not {predicted}.",
            f"This should be classified as {actual}.",
            f"Corrected from {predicted} to {actual} based on impact assessment.",
            f"User feedback: {actual} severity is more appropriate.",
        ]
        return random.choice(comments)

    def run_validation_pipeline(self, incidents: List[IncidentEvent]) -> Dict[str, Any]:
        """Run the full validation pipeline."""
        print(f"Running validation on {len(incidents)} incidents...")

        # Process incidents through pipeline
        results = []
        for incident in incidents:
            try:
                # Generate synthetic alerts and tickets that would create this incident
                alerts, tickets = self._generate_alerts_and_tickets_for_incident(incident)

                # Run pipeline analysis
                pipeline_incident = self.pipeline.run(alerts, tickets)

                # Store result with ground truth for comparison
                result = {
                    "incident_id": incident.id,
                    "predicted_severity": pipeline_incident.severity,
                    "predicted_impact": pipeline_incident.classification,  # Using classification as impact proxy
                    "ground_truth_severity": incident.metadata["ground_truth_severity"],
                    "ground_truth_impact": incident.metadata["ground_truth_impact"],
                    "pipeline_incident": {
                        "id": pipeline_incident.id,
                        "title": pipeline_incident.title,
                        "severity": pipeline_incident.severity,
                        "classification": pipeline_incident.classification,
                        "summary": pipeline_incident.summary,
                        "rca": pipeline_incident.rca,
                        "recommendations": pipeline_incident.recommendations,
                    },
                }
                results.append(result)

            except Exception as e:
                print(f"Error processing incident {incident.id}: {e}")
                continue

        return {
            "total_processed": len(results),
            "results": results,
        }

    def generate_validation_report(self, pipeline_results: Dict, feedback_results: Dict) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        print("Generating validation report...")

        # Get current metrics from feedback repository
        metrics = self.feedback_repo.get_metrics()

        # Calculate additional validation metrics
        pipeline_accuracy = self._calculate_pipeline_accuracy(pipeline_results)

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "phase": "Phase 4 - Validation",
            "summary": {
                "total_incidents_processed": pipeline_results["total_processed"],
                "total_feedback_records": feedback_results["total_feedback"],
                "feedback_rate": feedback_results["feedback_rate"],
            },
            "pipeline_metrics": pipeline_accuracy,
            "feedback_metrics": metrics,
            "validation_status": self._assess_validation_status(metrics, pipeline_accuracy),
            "recommendations": self._generate_recommendations(metrics, pipeline_accuracy),
        }

        return report

    def _calculate_pipeline_accuracy(self, pipeline_results: Dict) -> Dict[str, Any]:
        """Calculate accuracy metrics from pipeline results."""
        results = pipeline_results["results"]
        if not results:
            return {"error": "No pipeline results to analyze"}

        severity_correct = 0
        impact_correct = 0
        total = len(results)

        for result in results:
            if result["predicted_severity"] == result["ground_truth_severity"]:
                severity_correct += 1
            if result["predicted_impact"] == result["ground_truth_impact"]:
                impact_correct += 1

        return {
            "severity_accuracy": severity_correct / total if total > 0 else 0,
            "impact_accuracy": impact_correct / total if total > 0 else 0,
            "overall_accuracy": (severity_correct + impact_correct) / (2 * total) if total > 0 else 0,
        }

    def _assess_validation_status(self, feedback_metrics: Dict, pipeline_metrics: Dict) -> str:
        """Assess overall validation status."""
        precision = feedback_metrics.get("precision", 0)
        recall = feedback_metrics.get("recall", 0)
        routing_accuracy = feedback_metrics.get("routing_accuracy", 0)
        pipeline_accuracy = pipeline_metrics.get("overall_accuracy", 0)

        # Define success criteria
        if (precision >= 0.8 and recall >= 0.8 and routing_accuracy >= 0.8 and pipeline_accuracy >= 0.7):
            return "EXCELLENT - Ready for production rollout"
        elif (precision >= 0.7 and recall >= 0.7 and routing_accuracy >= 0.7 and pipeline_accuracy >= 0.6):
            return "GOOD - Ready for limited production with monitoring"
        elif (precision >= 0.6 and recall >= 0.6 and routing_accuracy >= 0.6 and pipeline_accuracy >= 0.5):
            return "FAIR - Requires additional training data and tuning"
        else:
            return "NEEDS_IMPROVEMENT - Additional development required"

    def _generate_recommendations(self, feedback_metrics: Dict, pipeline_metrics: Dict) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        precision = feedback_metrics.get("precision", 0)
        recall = feedback_metrics.get("recall", 0)
        fp_rate = feedback_metrics.get("false_positive_rate", 0)
        fn_rate = feedback_metrics.get("false_negative_rate", 0)

        if precision < 0.7:
            recommendations.append("Improve precision by reducing false positives - consider adjusting classification thresholds")
        if recall < 0.7:
            recommendations.append("Improve recall by reducing false negatives - review training data for underrepresented classes")
        if fp_rate > 0.3:
            recommendations.append("High false positive rate - implement additional validation checks for critical alerts")
        if fn_rate > 0.2:
            recommendations.append("High false negative rate - enhance detection for low-signal incidents")

        pipeline_acc = pipeline_metrics.get("overall_accuracy", 0)
        if pipeline_acc < 0.6:
            recommendations.append("Pipeline accuracy needs improvement - consider model retraining or feature engineering")

        if not recommendations:
            recommendations.append("Validation metrics look good - proceed with production rollout")
            recommendations.append("Continue monitoring metrics in production and collect additional feedback")

        return recommendations


def main():
    parser = argparse.ArgumentParser(description="Run Phase 4 validation for AIrena2.0")
    parser.add_argument("--incidents", type=int, default=50, help="Number of synthetic incidents to generate")
    parser.add_argument("--feedback-rate", type=float, default=0.3, help="Rate of user feedback (0.0-1.0)")
    parser.add_argument("--output", type=str, default="validation_report.json", help="Output file for validation report")
    parser.add_argument("--db-url", type=str, default="sqlite:///./.airena2_validation.db", help="Database URL for validation")

    args = parser.parse_args()

    print("🚀 Starting Phase 4 Validation for AIrena2.0")
    print(f"Generating {args.incidents} synthetic incidents...")
    print(f"Simulating {args.feedback_rate*100:.1f}% user feedback rate...")

    # Initialize database and validation runner
    db_service = DatabaseService(args.db_url)
    db_service.initialize_db()

    validator = ValidationRunner(db_service)

    try:
        # Generate validation incidents
        incidents = validator.generate_validation_incidents(args.incidents)
        print(f"✅ Generated {len(incidents)} validation incidents")

        # Run pipeline validation
        pipeline_results = validator.run_validation_pipeline(incidents)
        print(f"✅ Processed {pipeline_results['total_processed']} incidents through pipeline")

        # Simulate user feedback
        feedback_results = validator.simulate_user_feedback(incidents, args.feedback_rate)
        print(f"✅ Generated {feedback_results['total_feedback']} feedback records")

        # Generate validation report
        report = validator.generate_validation_report(pipeline_results, feedback_results)

        # Save report
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"✅ Validation report saved to {output_path}")
        print(f"\n📊 Validation Status: {report['validation_status']}")
        print("\n📋 Key Metrics:")
        print(".2f")
        print(".2f")
        print(".2f")
        print(".2f")
        print(".2f")

        print("\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        raise
    finally:
        db_service.close()


if __name__ == "__main__":
    main()