"""
Credit Protection Background Monitor Service
Runs scheduled tasks for quota resets, alerts, and health checks.
"""

import asyncio
import logging
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import httpx

from vaal_ai_empire.credit_protection.manager import get_manager

logger = logging.getLogger(__name__)


class AlertService:
    """Service for sending alerts about quota usage."""

    def __init__(self):
        self.email_enabled = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
        self.webhook_enabled = os.getenv("ALERT_WEBHOOK_ENABLED", "false").lower() == "true"

        # Email config
        self.email_to = os.getenv("ALERT_EMAIL_TO", "")
        self.email_from = os.getenv("ALERT_EMAIL_FROM", "")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")

        # Webhook config
        self.webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")

    async def send_alert(self, subject: str, message: str, level: str = "warning"):
        """Send alert via configured channels."""
        if self.email_enabled:
            await self._send_email_alert(subject, message)

        if self.webhook_enabled:
            await self._send_webhook_alert(subject, message, level)

    async def _send_email_alert(self, subject: str, message: str):
        """Send email alert."""
        if not all([self.email_to, self.email_from, self.smtp_user, self.smtp_password]):
            logger.warning("Email alerts not fully configured")
            return

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[VAAL AI Empire] {subject}"
            msg["From"] = self.email_from
            msg["To"] = self.email_to

            # Create HTML version
            html_body = f"""
            <html>
              <head></head>
              <body>
                <h2>{subject}</h2>
                <pre>{message}</pre>
                <hr>
                <p><small>Sent from VAAL AI Empire Credit Protection System</small></p>
              </body>
            </html>
            """

            part = MIMEText(html_body, "html")
            msg.attach(part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email alert sent: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_webhook_alert(self, subject: str, message: str, level: str):
        """Send webhook alert (Slack/Discord/Custom)."""
        if not self.webhook_url:
            logger.warning("Webhook URL not configured")
            return

        try:
            # Format for Slack/Discord
            payload = {
                "text": f"🚨 {subject}",
                "attachments": [
                    {
                        "color": self._get_color_for_level(level),
                        "text": message,
                        "footer": "VAAL AI Empire Credit Protection",
                        "ts": int(datetime.now().timestamp()),
                    }
                ],
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload, timeout=10.0)
                response.raise_for_status()

            logger.info(f"Webhook alert sent: {subject}")

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    def _get_color_for_level(self, level: str) -> str:
        """Get color code for alert level."""
        colors = {
            "critical": "#ff0000",
            "error": "#ff6600",
            "warning": "#ffcc00",
            "info": "#00ccff",
        }
        return colors.get(level, colors["info"])


class CreditMonitorService:
    """Background service for credit protection monitoring."""

    def __init__(self):
        self.credit_manager = get_manager()
        self.alert_service = AlertService()
        self.running = False

        # Alert thresholds (% of daily limit)
        self.warning_threshold = 70
        self.critical_threshold = 90

        # Track if we've already sent alerts
        self.warning_sent = False
        self.critical_sent = False

    async def start(self):
        """Start the monitoring service."""
        self.running = True
        logger.info("Credit monitoring service started")

        # Start background tasks
        await asyncio.gather(
            self._hourly_reset_task(),
            self._daily_reset_task(),
            self._usage_monitor_task(),
            return_exceptions=True,
        )

    async def stop(self):
        """Stop the monitoring service."""
        self.running = False
        logger.info("Credit monitoring service stopped")

    async def _hourly_reset_task(self):
        """Task to reset hourly usage counters."""
        while self.running:
            try:
                # Wait until next hour
                now = datetime.now()
                next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                wait_seconds = (next_hour - now).total_seconds()

                logger.info(f"Next hourly reset in {wait_seconds:.0f} seconds")
                await asyncio.sleep(wait_seconds)

                # Reset hourly usage
                self.credit_manager.reset_hourly_usage()
                logger.info("✅ Hourly usage counters reset")

            except Exception as e:
                logger.error(f"Error in hourly reset task: {e}")
                await asyncio.sleep(60)

    async def _daily_reset_task(self):
        """Task to reset daily usage counters."""
        while self.running:
            try:
                # Wait until midnight
                now = datetime.now()
                tomorrow = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1)
                wait_seconds = (tomorrow - now).total_seconds()

                logger.info(f"Next daily reset in {wait_seconds:.0f} seconds")
                await asyncio.sleep(wait_seconds)

                # Reset daily usage
                self.credit_manager.reset_daily_usage()

                # Reset alert flags
                self.warning_sent = False
                self.critical_sent = False

                logger.info("✅ Daily usage counters reset")

                await self.alert_service.send_alert(
                    subject="Daily Usage Reset",
                    message="Daily credit usage counters have been reset.",
                    level="info",
                )

            except Exception as e:
                logger.error(f"Error in daily reset task: {e}")
                await asyncio.sleep(60)

    async def _usage_monitor_task(self):
        """Task to monitor usage and send alerts."""
        while self.running:
            try:
                usage = self.credit_manager.get_usage_summary()
                daily = usage["daily"]

                # Check usage percentages
                max_usage_percent = max(
                    daily["usage_percent"]["requests"],
                    daily["usage_percent"]["tokens"],
                    daily["usage_percent"]["cost"],
                )

                # Critical alert (90%+)
                if max_usage_percent >= self.critical_threshold and not self.critical_sent:
                    await self._send_critical_alert(usage)
                    self.critical_sent = True

                    # Trigger circuit breaker if usage is very high
                    if max_usage_percent >= 95:
                        self.credit_manager.trigger_circuit_breaker(duration_minutes=60)
                        await self.alert_service.send_alert(
                            subject="🚨 CIRCUIT BREAKER ACTIVATED",
                            message=(
                                f"Circuit breaker activated due to usage "
                                f"({max_usage_percent:.1f}%).\n"
                                f"All LLM requests will be blocked for 60 minutes."
                            ),
                            level="critical",
                        )

                # Warning alert (70%+)
                elif max_usage_percent >= self.warning_threshold and not self.warning_sent:
                    await self._send_warning_alert(usage)
                    self.warning_sent = True

                # Wait 5 minutes before next check
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"Error in usage monitor task: {e}")
                await asyncio.sleep(60)

    async def _send_warning_alert(self, usage: dict):
        """Send warning alert when usage reaches threshold."""
        daily = usage["daily"]

        message = f"""
⚠️  Credit Usage Warning

Your daily credit usage has reached the warning threshold.

Current Usage:
- Requests: {daily['requests']} / {daily['limits']['requests']} \
({daily['usage_percent']['requests']:.1f}%)
- Tokens: {daily['tokens']:,} / {daily['limits']['tokens']:,} \
({daily['usage_percent']['tokens']:.1f}%)
- Cost: ${daily['cost_usd']:.4f} / ${daily['limits']['cost_usd']:.2f} \
({daily['usage_percent']['cost']:.1f}%)

Tier: {usage['tier'].upper()}

Please monitor your usage to avoid hitting daily limits.
        """

        await self.alert_service.send_alert(
            subject="⚠️  Credit Usage Warning (70% threshold)", message=message, level="warning"
        )

        log_msg = f"Usage warning sent: {daily['usage_percent']['requests']:.1f}% of daily limit"
        logger.warning(log_msg)

    async def _send_critical_alert(self, usage: dict):
        """Send critical alert when usage nears limit."""
        daily = usage["daily"]

        message = f"""
🚨 CRITICAL: Credit Usage Alert

Your daily credit usage is approaching the limit!

Current Usage:
- Requests: {daily['requests']} / {daily['limits']['requests']} \
({daily['usage_percent']['requests']:.1f}%)
- Tokens: {daily['tokens']:,} / {daily['limits']['tokens']:,} \
({daily['usage_percent']['tokens']:.1f}%)
- Cost: ${daily['cost_usd']:.4f} / ${daily['limits']['cost_usd']:.2f} \
({daily['usage_percent']['cost']:.1f}%)

Tier: {usage['tier'].upper()}

⚠️  WARNING: Circuit breaker may activate at 95% usage.
New requests will be blocked to prevent cost overruns.

Consider:
1. Reducing request frequency
2. Waiting for daily reset (midnight)
3. Upgrading to a higher tier
        """

        await self.alert_service.send_alert(
            subject="🚨 CRITICAL: Credit Usage Alert (90% threshold)",
            message=message,
            level="critical",
        )

        log_msg = f"Critical usage alert sent: {daily['usage_percent']['requests']:.1f}% limit"
        logger.error(log_msg)


# Global service instance
_monitor_service: Optional[CreditMonitorService] = None


def get_monitor_service() -> CreditMonitorService:
    """Get global monitor service instance."""
    global _monitor_service

    if _monitor_service is None:
        _monitor_service = CreditMonitorService()

    return _monitor_service


async def start_monitor_service():
    """Start the credit monitoring service."""
    service = get_monitor_service()
    await service.start()


if __name__ == "__main__":
    # Run as standalone service
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    asyncio.run(start_monitor_service())
