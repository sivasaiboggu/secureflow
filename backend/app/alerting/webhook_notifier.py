import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class WebhookNotifier:
    """Dispatches finding event payloads to user-configured custom endpoint URLs"""
    
    def dispatch_payload(self, target_url: str, payload: Dict[str, Any]) -> bool:
        try:
            response = httpx.post(target_url, json=payload, timeout=8.0)
            if response.status_code in [200, 201, 202]:
                logger.info(f"Webhook event payload successfully dispatched to: {target_url}")
                return True
            else:
                logger.error(f"Webhook endpoint returned error status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed sending webhook to {target_url}: {e}")
            return False

webhook_notifier = WebhookNotifier()
