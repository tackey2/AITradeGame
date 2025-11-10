"""
Notification System
Sends notifications via console (and email if configured)
"""
from datetime import datetime
from typing import Optional


class Notifier:
    """Simple notification system"""

    def __init__(self, db, email_enabled: bool = False):
        """
        Args:
            db: Database instance
            email_enabled: Whether to send email notifications
        """
        self.db = db
        self.email_enabled = email_enabled

    def send_notification(self, title: str, message: str,
                         priority: str = "medium", model_id: Optional[int] = None):
        """
        Send a notification

        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (low, medium, high, critical)
            model_id: Model ID (optional)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Console notification (always)
        priority_icons = {
            'low': 'ℹ️',
            'medium': '⚠️',
            'high': '🔴',
            'critical': '🚨'
        }
        icon = priority_icons.get(priority, 'ℹ️')

        print(f"\n{icon} [{timestamp}] {title}")
        print(f"   {message}\n")

        # Log to database
        if model_id:
            severity_map = {
                'low': 'low',
                'medium': 'medium',
                'high': 'high',
                'critical': 'critical'
            }
            self.db.log_incident(
                model_id=model_id,
                incident_type='NOTIFICATION',
                severity=severity_map.get(priority, 'medium'),
                message=f"{title}: {message}"
            )

        # TODO: Email notification (if enabled)
        if self.email_enabled and priority in ['high', 'critical']:
            self._send_email(title, message)

    def _send_email(self, title: str, message: str):
        """Send email notification (placeholder)"""
        # TODO: Implement email sending with SMTP
        print(f"[EMAIL] Would send: {title}")
        pass
