import httpx
import logging
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)

class PagerDutyNotifier:
    """Invokes PagerDuty Events API v2 to trigger operational alerts for on-call escalations"""
    
    def __init__(self, routing_key: Optional[str] = None):
        self.routing_key = routing_key or settings.PAGERDUTY_API_KEY
        self.api_url = "https://events.pagerduty.com/v2/enqueue"

    def trigger_incident(self, title: str, severity: str, source: str, details: str) -> bool:
        if not self.routing_key:
            logger.info(f"PagerDuty incident simulated: [{severity}] {title} on {source}")
            return True
            
        # PagerDuty severity mapping: critical, error, warning, info
        pd_severity = "critical" if severity.upper() in ["CRITICAL", "HIGH"] else "warning"
        
        payload = {
            "routing_key": self.routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": title,
                "severity": pd_severity,
                "source": source,
                "custom_details": {
                    "vulnerability_info": details
                }
            }
        }
        
        try:
            response = httpx.post(self.api_url, json=payload, timeout=5.0)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed sending PagerDuty incident: {e}")
            return False

pagerduty_notifier = PagerDutyNotifier()
