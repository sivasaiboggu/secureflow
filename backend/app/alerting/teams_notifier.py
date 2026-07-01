import httpx
import logging
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)

class TeamsNotifier:
    """Dispatches card-formatted compliance metrics to Microsoft Teams channels"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.TEAMS_WEBHOOK_URL

    def send_card(self, title: str, message: str, severity: str, resource_id: str) -> bool:
        if not self.webhook_url:
            logger.info(f"Teams Card simulated: [{severity}] {title} - {message}")
            return True
            
        color = "FF1744" if severity.upper() == "CRITICAL" else "FF9100" if severity.upper() == "HIGH" else "00E676"
        
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": f"SecureFlow Alert: {title}",
            "sections": [{
                "activityTitle": f"Vulnerability Alert: {title}",
                "activitySubtitle": f"Severity Level: {severity}",
                "facts": [
                    {"name": "Resource Identifier", "value": resource_id},
                    {"name": "Description Details", "value": message}
                ],
                "markdown": True
            }]
        }
        
        try:
            response = httpx.post(self.webhook_url, json=card, timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed sending Teams card notification: {e}")
            return False

teams_notifier = TeamsNotifier()
