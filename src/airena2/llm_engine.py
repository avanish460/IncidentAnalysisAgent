from __future__ import annotations

import json
import os
from typing import Any, List

import requests
from requests import HTTPError

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass  # python-dotenv not installed, continue without it

from .data_models import IncidentEvent

DEFAULT_MODEL = "gpt-4.1"
DEFAULT_API_VERSION = "2024-12-01-preview"


class LLMEngine:
    """OpenAI-compatible REST engine for custom GPT deployments."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing OPENAI_API_KEY environment variable.")

        self.api_base = os.environ.get("OPENAI_API_BASE")
        if not self.api_base:
            raise ValueError("Missing OPENAI_API_BASE environment variable.")

        self.api_version = os.environ.get("OPENAI_API_VERSION", DEFAULT_API_VERSION)
        self.model = os.environ.get("OPENAI_MODEL", model)

    def _build_context(self, incident: IncidentEvent) -> str:
        alerts = "\n".join(
            [f"- [{alert.severity}] {alert.source}: {alert.message}" for alert in incident.alerts]
        )
        tickets = "\n".join(
            [f"- [{ticket.priority}] {ticket.summary}: {ticket.description}" for ticket in incident.tickets]
        )
        return (
            f"Incident title: {incident.title}\n"
            f"Severity: {incident.severity}\n"
            f"Classification: {incident.classification}\n"
            f"Alerts:\n{alerts if alerts else '- none'}\n"
            f"Tickets:\n{tickets if tickets else '- none'}\n"
        )

    def _call_llm(self, prompt: str) -> str:
        request_url = f"{self.api_base.rstrip('/')}/chat/completions?api-version={self.api_version}"
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert incident response analyst."},
                {"role": "user", "content": prompt},
            ],
            "maxTokens": 400,
            "temperature": 0.2,
        }

        try:
            response = requests.post(request_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except HTTPError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}, response={response.text}") from exc
        except (KeyError, IndexError, ValueError) as exc:
            raise RuntimeError(f"Unexpected LLM response format: {response.text}") from exc

    def summarize_incident(self, incident: IncidentEvent) -> str:
        context = self._build_context(incident)
        prompt = (
            "Create a concise incident summary for an operations engineer using the data below. "
            "Focus on the main impact, affected service, and what is known so far.\n\n"
            f"{context}"
        )
        return self._call_llm(prompt)

    def generate_rca(self, incident: IncidentEvent) -> str:
        context = self._build_context(incident)
        prompt = (
            "Analyze the incident context below and provide the most likely root cause or failure mode. "
            "Include any high-level reasoning.\n\n"
            f"{context}"
        )
        return self._call_llm(prompt)

    def recommend_actions(self, incident: IncidentEvent) -> List[str]:
        context = self._build_context(incident)
        prompt = (
            "Given this incident context, suggest the top 3 remediation or next-step actions "
            "an on-call engineer should take. Return the actions as a short bullet list.\n\n"
            f"{context}"
        )
        answer = self._call_llm(prompt)
        return [line.strip(" -") for line in answer.splitlines() if line.strip()]
