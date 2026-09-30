"""Re-export shared alert module for service use."""
from shared.models.alert import Alert, AlertType

__all__ = ["Alert", "AlertType"]
