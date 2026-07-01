import httpx
import logging
from typing import Dict, Any, Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)

class SlackNotifier:
    """Posts structured warning messages to Slack channels using Webhooks"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.SLACK_WEBHOOK_URL

    def send_alert(self, title: str, message: str, severity: str, resource_id: str) -> bool:
        if not self.webhook_url:
            logger.info(f"Slack Notification simulated: [{severity}] {title} - {message}")
            return True
            
        color = "#ff1744" if severity.upper() == "CRITICAL" else "#ff9100" if severity.upper() == "HIGH" else "#29b6f6"
        
        payload = {
            "attachments": [
                {
                    "fallback": f"[{severity}] {title}",
                    "color": color,
                    "title": f"SecureFlow Alert: {title}",
                    "fields": [
                        {"title": "Severity", "value": severity.upper(), "short": True},
                        {"title": "Resource", "value": resource_id, "short": True},
                        {"title": "Details", "value": message, "short": False}
                    ],
                    "footer": "SecureFlow CSPM Engine",
                    "ts": int(httpx.Client().get("http://worldtimeapi.org/api/timezone/Etc/UTC").json().get("unixtime", 0)) if not settings.DEBUG else 0
                }
            ]
        }
        
        try:
            response = httpx.post(self.webhook_url, json=payload, timeout=5.0)
            if response.status_code == 200:
                logger.info("Slack alert posted successfully.")
                return True
            else:
                logger.error(f"Slack webhook returned non-200 code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed sending Slack notification: {e}")
            return False

slack_notifier = SlackNotifier()
