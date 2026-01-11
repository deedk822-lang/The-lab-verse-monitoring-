"""
Self-Healing Agent for Prometheus AlertManager Integration
===========================================================

Processes Prometheus AlertManager webhook payloads and generates safe,
actionable remediation blueprints using AI models (OpenAI/Anthropic).

Features:
- Async-first architecture
- Retry logic with exponential backoff
- Input validation with Pydantic
- Safety checks for destructive operations
- Comprehensive error handling
- Observability (metrics, logging, tracing)
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import backoff
import httpx
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field, ValidationError, field_validator

# ============================================================================
# LOGGING & METRICS
# ============================================================================

logger = logging.getLogger(__name__)

# Prometheus metrics
healer_requests_total = Counter(
    "healer_requests_total",
    "Total healing requests processed",
    ["status"]
)

healer_duration_seconds = Histogram(
    "healer_duration_seconds",
    "Time spent processing healing requests"
)

openai_api_calls_total = Counter(
    "openai_api_calls_total",
    "Total OpenAI API calls",
    ["status"]
)

# ============================================================================
# PYDANTIC MODELS - Input Validation
# ============================================================================

class AlertStatus(str, Enum):
    """Alert status from Prometheus AlertManager"""
    FIRING = "firing"
    RESOLVED = "resolved"


class AlertSeverity(str, Enum):
    """Standard alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class PromAlert(BaseModel):
    """Single alert from Prometheus AlertManager"""
    status: AlertStatus
    labels: Dict[str, str]
    annotations: Dict[str, str] = Field(default_factory=dict)
    starts_at: Optional[datetime] = Field(None, alias="startsAt")
    ends_at: Optional[datetime] = Field(None, alias="endsAt")
    generator_url: Optional[str] = Field(None, alias="generatorURL")
    fingerprint: Optional[str] = None

    @field_validator("labels")
    @classmethod
    def validate_required_labels(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Ensure required labels are present"""
        required = {"alertname"}
        if not required.issubset(v.keys()):
            raise ValueError(f"Missing required labels: {required - v.keys()}")
        return v

    @property
    def severity(self) -> AlertSeverity:
        """Extract severity from labels"""
        severity = self.labels.get("severity", "info").lower()
        try:
            return AlertSeverity(severity)
        except ValueError:
            return AlertSeverity.INFO


class AlertPayload(BaseModel):
    """Complete AlertManager webhook payload"""
    receiver: str
    status: AlertStatus
    alerts: List[PromAlert]
    group_labels: Dict[str, str] = Field(default_factory=dict, alias="groupLabels")
    common_labels: Dict[str, str] = Field(default_factory=dict, alias="commonLabels")
    common_annotations: Dict[str, str] = Field(
        default_factory=dict, alias="commonAnnotations"
    )
    external_url: Optional[str] = Field(None, alias="externalURL")
    version: str = "4"
    group_key: Optional[str] = Field(None, alias="groupKey")

    @field_validator("alerts")
    @classmethod
    def validate_alerts_not_empty(cls, v: List[PromAlert]) -> List[PromAlert]:
        """Ensure at least one alert is present"""
        if not v:
            raise ValueError("Alerts list cannot be empty")
        return v


# ============================================================================
# OUTPUT MODELS
# ============================================================================

class ImpactLevel(str, Enum):
    """Estimated impact of remediation"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MANUAL_REVIEW = "manual_review"


class BlueprintResult(BaseModel):
    """Result of healing agent processing"""
    blueprint: str = Field(..., description="Generated remediation blueprint")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )
    estimated_impact: ImpactLevel = Field(
        ..., description="Estimated impact of applying this blueprint"
    )
    requires_approval: bool = Field(
        ..., description="Whether manual approval is required"
    )
    rollback_plan: Optional[str] = Field(
        None, description="Rollback procedure if available"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


# ============================================================================
# SAFETY VALIDATOR
# ============================================================================

class SafetyValidator:
    """Validates blueprints for safety and security"""

    # Destructive patterns that require manual approval
    DESTRUCTIVE_PATTERNS = [
        r"\brm\s+-rf\b",
        r"\bdd\s+if=",
        r"\bmkfs\b",
        r"\bformat\b",
        r"\bshutdown\b",
        r"\bpoweroff\b",
        r"\breboot\s+-f\b",
        r"\bkill\s+-9\s+1\b",  # init process
        r"\b>\s*/dev/sd[a-z]\b",  # direct disk write
        r"\biptables\s+-F\b",  # flush firewall rules
        r"\bsudo\s+rm\b",
    ]

    # Suspicious patterns that need review
    SUSPICIOUS_PATTERNS = [
        r"curl\s+.*\|\s*(?:bash|sh)",  # pipe to shell
        r"wget\s+.*\|\s*(?:bash|sh)",
        r"eval\s*\(",  # eval in scripts
        r"exec\s*\(",
    ]

    @classmethod
    def validate(cls, blueprint: str) -> tuple[bool, List[str]]:
        """
        Validate blueprint safety.

        Returns:
            (is_safe, violations)
        """
        violations: List[str] = []

        # Check destructive patterns
        for pattern in cls.DESTRUCTIVE_PATTERNS:
            if re.search(pattern, blueprint, re.IGNORECASE | re.MULTILINE):
                violations.append(
                    f"Destructive operation detected: {pattern}"
                )

        # Check suspicious patterns
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, blueprint, re.IGNORECASE | re.MULTILINE):
                violations.append(
                    f"Suspicious operation detected: {pattern}"
                )

        is_safe = len(violations) == 0
        return is_safe, violations


# ============================================================================
# SELF-HEALING AGENT
# ============================================================================

@dataclass
class SelfHealingAgent:
    """
    AI-powered self-healing agent for alert remediation.

    Processes Prometheus AlertManager payloads and generates safe,
    actionable remediation blueprints.
    """

    # Configuration
    openai_api_key: Optional[str] = None
    model: str = "gpt-4-turbo-preview"
    max_tokens: int = 2000
    timeout: int = 60
    max_retries: int = 5

    # Internal state
    _client: Optional[AsyncOpenAI] = field(default=None, init=False, repr=False)
    _safety_validator: SafetyValidator = field(
        default_factory=SafetyValidator, init=False, repr=False
    )

    def __post_init__(self) -> None:
        """Initialize the OpenAI client"""
        api_key = self.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass openai_api_key parameter."
            )

        self._client = AsyncOpenAI(
            api_key=api_key,
            timeout=self.timeout,
            max_retries=0,  # We handle retries manually with backoff
        )
        logger.info(
            "SelfHealingAgent initialized",
            extra={"model": self.model, "timeout": self.timeout}
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    @healer_duration_seconds.time()
    async def process_alert(self, alert_data: dict) -> Dict[str, Any]:
        """
        Process an alert and generate remediation blueprint.

        Args:
            alert_data: Raw alert payload from AlertManager

        Returns:
            Dictionary containing blueprint and metadata

        Raises:
            ValueError: If alert data is invalid
            RuntimeError: If blueprint generation fails
        """
        try:
            # Validate input
            payload = self._validate_alert_payload(alert_data)
            logger.info(
                "Processing alert",
                extra={
                    "receiver": payload.receiver,
                    "status": payload.status,
                    "alert_count": len(payload.alerts)
                }
            )

            # Generate blueprint
            blueprint = await self._generate_blueprint(payload)

            # Validate safety
            is_safe, violations = self._safety_validator.validate(blueprint)

            # Build result
            result = self._build_result(
                blueprint=blueprint,
                payload=payload,
                is_safe=is_safe,
                violations=violations
            )

            healer_requests_total.labels(status="success").inc()
            logger.info("Alert processing completed", extra={"is_safe": is_safe})

            return result.model_dump()

        except ValidationError as e:
            healer_requests_total.labels(status="validation_error").inc()
            logger.error("Alert validation failed", extra={"error": str(e)})
            raise ValueError(f"Invalid alert payload: {e}")

        except Exception as e:
            healer_requests_total.labels(status="error").inc()
            logger.exception("Alert processing failed")
            raise RuntimeError(f"Failed to process alert: {e}")

    # ========================================================================
    # INTERNAL METHODS
    # ========================================================================

    def _validate_alert_payload(self, alert_data: dict) -> AlertPayload:
        """Validate and parse alert payload"""
        try:
            return AlertPayload(**alert_data)
        except ValidationError as e:
            logger.error(
                "Alert payload validation failed",
                extra={"errors": e.errors()}
            )
            raise

    @backoff.on_exception(
        backoff.expo,
        (APIError, RateLimitError, APITimeoutError, httpx.HTTPError),
        max_tries=5,
        factor=2,
        max_value=60,
        jitter=backoff.random_jitter,
    )
    async def _call_openai(self, prompt: str) -> str:
        """
        Call OpenAI API with retry logic.

        Args:
            prompt: The prompt to send to OpenAI

        Returns:
            Generated text response

        Raises:
            APIError: If API call fails after retries
        """
        try:
            logger.debug("Calling OpenAI API", extra={"model": self.model})

            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,  # Lower temperature for more consistent output
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI returned empty response")

            openai_api_calls_total.labels(status="success").inc()
            logger.debug(
                "OpenAI API call successful",
                extra={"tokens_used": response.usage.total_tokens if response.usage else None}
            )

            return content

        except RateLimitError as e:
            openai_api_calls_total.labels(status="rate_limit").inc()
            logger.warning("OpenAI rate limit hit, retrying...", extra={"error": str(e)})
            raise

        except APITimeoutError as e:
            openai_api_calls_total.labels(status="timeout").inc()
            logger.warning("OpenAI API timeout, retrying...", extra={"error": str(e)})
            raise

        except APIError as e:
            openai_api_calls_total.labels(status="error").inc()
            logger.error("OpenAI API error", extra={"error": str(e)})
            raise

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI model"""
        return """You are a DevOps and SRE expert assistant specialized in creating safe,
actionable remediation blueprints for production incidents.

Your responsibilities:
1. Analyze Prometheus AlertManager alerts
2. Generate SAFE remediation steps (bash, terraform, kubectl, etc.)
3. Include rollback procedures
4. Flag destructive operations for manual approval

Safety requirements:
- NEVER include destructive commands (rm -rf, dd, format, shutdown)
- If destructive changes are needed, respond with "REQUIRES_MANUAL_APPROVAL"
- Always provide rollback steps
- Include validation steps before and after changes
- Consider impact on production systems

Output format:
Provide a structured blueprint with:
1. Problem Summary
2. Root Cause Analysis
3. Remediation Steps (with exact commands)
4. Validation Steps
5. Rollback Procedure
6. Monitoring Recommendations

Be concise but complete. Focus on production safety."""

    async def _generate_blueprint(self, payload: AlertPayload) -> str:
        """
        Generate remediation blueprint for alert payload.

        Args:
            payload: Validated alert payload

        Returns:
            Generated blueprint text
        """
        # Extract relevant information
        alert_info = self._extract_alert_info(payload)

        # Build prompt
        prompt = self._build_prompt(payload, alert_info)

        # Call OpenAI
        blueprint = await self._call_openai(prompt)

        return blueprint

    def _extract_alert_info(self, payload: AlertPayload) -> Dict[str, Any]:
        """Extract key information from alert payload"""
        alerts = payload.alerts
        
        # Group alerts by name and severity
        alert_groups: Dict[str, List[PromAlert]] = {}
        for alert in alerts:
            name = alert.labels.get("alertname", "unknown")
            if name not in alert_groups:
                alert_groups[name] = []
            alert_groups[name].append(alert)
        
        # Find highest severity
        severities = [alert.severity for alert in alerts]
        highest_severity = (
            AlertSeverity.CRITICAL if AlertSeverity.CRITICAL in severities
            else AlertSeverity.WARNING if AlertSeverity.WARNING in severities
            else AlertSeverity.INFO
        )
        
        return {
            "alert_groups": alert_groups,
            "highest_severity": highest_severity,
            "firing_count": len([a for a in alerts if a.status == AlertStatus.FIRING]),
            "resolved_count": len([a for a in alerts if a.status == AlertStatus.RESOLVED]),
            "common_labels": payload.common_labels,
            "common_annotations": payload.common_annotations,
        }

    def _build_prompt(self, payload: AlertPayload, alert_info: Dict[str, Any]) -> str:
        """Build the prompt for OpenAI"""
        firing_alerts = [a for a in payload.alerts if a.status == AlertStatus.FIRING]

        prompt_parts = [
            "# Prometheus Alert Remediation Request",
            "",
            f"## Alert Summary",
            f"- Receiver: {payload.receiver}",
            f"- Overall Status: {payload.status}",
            f"- Severity: {alert_info['highest_severity'].value}",
            f"- Firing Alerts: {alert_info['firing_count']}",
            f"- Resolved Alerts: {alert_info['resolved_count']}",
            "",
        ]

        # Add firing alerts details
        if firing_alerts:
            prompt_parts.extend([
                "## Firing Alerts Details",
                ""
            ])

            for i, alert in enumerate(firing_alerts[:5], 1):  # Limit to 5 alerts
                prompt_parts.extend([
                    f"### Alert {i}: {alert.labels.get('alertname', 'Unknown')}",
                    f"**Severity**: {alert.severity.value}",
                    f"**Started**: {alert.starts_at.isoformat() if alert.starts_at else 'Unknown'}",
                    "",
                    "**Labels**:",
                ])
                for key, value in alert.labels.items():
                    prompt_parts.append(f"- {key}: {value}")

                if alert.annotations:
                    prompt_parts.extend(["", "**Annotations**:"])
                    for key, value in alert.annotations.items():
                        prompt_parts.append(f"- {key}: {value}")

                prompt_parts.append("")

        # Add constraints
        prompt_parts.extend([
            "## Constraints",
            "- This is a PRODUCTION environment",
            "- Changes must be reversible",
            "- No destructive commands (rm -rf, dd, format, shutdown, poweroff)",
            "- If destructive changes are required, respond ONLY with: REQUIRES_MANUAL_APPROVAL",
            "- Include validation steps before applying changes",
            "- Provide complete rollback procedure",
            "",
            "## Required Output",
            "Generate a comprehensive remediation blueprint following the specified format.",
        ])

        return "\n".join(prompt_parts)

    def _build_result(
        self,
        blueprint: str,
        payload: AlertPayload,
        is_safe: bool,
        violations: List[str]
    ) -> BlueprintResult:
        """Build the final result object"""

        # Check if manual approval is required
        requires_approval = (
            not is_safe or
            "REQUIRES_MANUAL_APPROVAL" in blueprint or
            any(a.severity == AlertSeverity.CRITICAL for a in payload.alerts)
        )

        # Calculate confidence
        confidence = self._calculate_confidence(blueprint, is_safe, payload)

        # Determine impact level
        impact = self._assess_impact(blueprint, is_safe, payload)

        # Extract rollback plan if present
        rollback = self._extract_rollback_plan(blueprint)

        return BlueprintResult(
            blueprint=blueprint,
            confidence=confidence,
            estimated_impact=impact,
            requires_approval=requires_approval,
            rollback_plan=rollback,
            metadata={
                "alert_count": len(payload.alerts),
                "highest_severity": max(
                    (a.severity.value for a in payload.alerts),
                    default="info"
                ),
                "safety_violations": violations,
                "generated_at": datetime.utcnow().isoformat(),
            }
        )

    def _calculate_confidence(
        self,
        blueprint: str,
        is_safe: bool,
        payload: AlertPayload
    ) -> float:
        """Calculate confidence score for the blueprint"""
        confidence = 0.5  # Base confidence

        # Reduce confidence for unsafe blueprints
        if not is_safe:
            confidence -= 0.3

        # Reduce confidence for manual approval
        if "REQUIRES_MANUAL_APPROVAL" in blueprint:
            return 0.0

        # Increase confidence for well-structured output
        if "## Remediation Steps" in blueprint or "# Remediation" in blueprint:
            confidence += 0.1

        if "## Rollback" in blueprint or "rollback" in blueprint.lower():
            confidence += 0.1

        if "## Validation" in blueprint or "validation" in blueprint.lower():
            confidence += 0.1

        # Adjust for blueprint length (too short = low confidence)
        if len(blueprint) < 200:
            confidence -= 0.2
        elif len(blueprint) > 500:
            confidence += 0.1

        # Adjust for alert severity
        critical_count = sum(
            1 for a in payload.alerts if a.severity == AlertSeverity.CRITICAL
        )
        if critical_count > 0:
            confidence -= 0.1 * min(critical_count, 3)

        return max(0.0, min(1.0, confidence))

    def _assess_impact(
        self,
        blueprint: str,
        is_safe: bool,
        payload: AlertPayload
    ) -> ImpactLevel:
        """Assess the impact level of the blueprint"""
        if not is_safe or "REQUIRES_MANUAL_APPROVAL" in blueprint:
            return ImpactLevel.MANUAL_REVIEW

        # Check for high-impact operations
        high_impact_keywords = [
            "restart", "scale", "deploy", "migrate", "upgrade",
            "kubectl apply", "terraform apply", "helm upgrade"
        ]

        medium_impact_keywords = [
            "config", "setting", "parameter", "tune", "adjust"
        ]

        blueprint_lower = blueprint.lower()

        if any(kw in blueprint_lower for kw in high_impact_keywords):
            return ImpactLevel.HIGH

        if any(kw in blueprint_lower for kw in medium_impact_keywords):
            return ImpactLevel.MEDIUM

        # Check alert severity
        if any(a.severity == AlertSeverity.CRITICAL for a in payload.alerts):
            return ImpactLevel.HIGH

        return ImpactLevel.LOW

    def _extract_rollback_plan(self, blueprint: str) -> Optional[str]:
        """Extract rollback plan from blueprint if present"""
        # Look for rollback section
        patterns = [
            r"## Rollback.*?(?=##|\Z)",
            r"# Rollback.*?(?=#|\Z)",
            r"Rollback Procedure:.*?(?=\n\n|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, blueprint, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def process_prometheus_alert(
    alert_payload: dict,
    openai_api_key: Optional[str] = None,
    model: str = "gpt-4-turbo-preview"
) -> Dict[str, Any]:
    """
    Convenience function to process a Prometheus alert.

    Args:
        alert_payload: Raw alert payload from AlertManager
        openai_api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        model: OpenAI model to use

    Returns:
        Blueprint result dictionary

    Example:
        >>> result = await process_prometheus_alert({
        ...     "receiver": "team-x",
        ...     "status": "firing",
        ...     "alerts": [...]
        ... })
        >>> print(result["blueprint"])
    """
    agent = SelfHealingAgent(openai_api_key=openai_api_key, model=model)
    return await agent.process_alert(alert_payload)


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    "SelfHealingAgent",
    "AlertPayload",
    "PromAlert",
    "BlueprintResult",
    "AlertStatus",
    "AlertSeverity",
    "ImpactLevel",
    "SafetyValidator",
    "process_prometheus_alert",
]