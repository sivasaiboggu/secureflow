import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Delivers formatted alert emails for critical compliance breaches via SMTP configurations"""
    
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.sender = settings.SMTP_FROM

    def send_email(self, recipient: str, subject: str, html_content: str) -> bool:
        if not self.host or not self.user:
            logger.info(f"Email Notification simulated: Recipient={recipient} Subject={subject}")
            return True
            
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = recipient
        
        msg.attach(MIMEText(html_content, "html"))
        
        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.sender, recipient, msg.as_string())
            logger.info(f"Audit email dispatched successfully to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed sending alert email to {recipient}: {e}")
            return False

email_notifier = EmailNotifier()
