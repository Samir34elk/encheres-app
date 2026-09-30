"""Re-export shared user module for service use."""
from shared.models.user import User, UserRole, AuthProvider

__all__ = ["User", "UserRole", "AuthProvider"]
