"""
User model and authentication classes.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from .base import BaseModel

class UserRole(Enum):
    """User roles for access control."""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"

class UserStatus(Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"

class User(BaseModel):
    """User model for authentication and authorization."""
    
    def __init__(self, username: str, email: str, password: str = "", 
                 role: str = UserRole.USER.value, status: str = UserStatus.PENDING_VERIFICATION.value,
                 first_name: str = "", last_name: str = "", phone: str = "",
                 email_verified: bool = False, last_login: Optional[str] = None,
                 failed_login_attempts: int = 0, locked_until: Optional[str] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.email = email
        self.password_hash = self._hash_password(password) if password else ""
        self.role = role
        self.status = status
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email_verified = email_verified
        self.last_login = last_login
        self.failed_login_attempts = failed_login_attempts
        self.locked_until = locked_until
        self.email_verification_token = self._generate_token()
        self.password_reset_token = None
        self.password_reset_expires = None
    
    def _hash_password(self, password: str) -> str:
        """Hash password using PBKDF2 with salt."""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                      salt.encode('utf-8'), 100000)
        return f"{salt}:{pwd_hash.hex()}"
    
    def _generate_token(self) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        if not self.password_hash:
            return False
        
        try:
            salt, stored_hash = self.password_hash.split(':')
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                          salt.encode('utf-8'), 100000)
            return pwd_hash.hex() == stored_hash
        except ValueError:
            return False
    
    def set_password(self, password: str):
        """Set new password."""
        self.password_hash = self._hash_password(password)
        self.password_reset_token = None
        self.password_reset_expires = None
    
    def generate_password_reset_token(self) -> str:
        """Generate password reset token."""
        self.password_reset_token = self._generate_token()
        self.password_reset_expires = (datetime.now() + timedelta(hours=24)).isoformat()
        return self.password_reset_token
    
    def verify_password_reset_token(self, token: str) -> bool:
        """Verify password reset token."""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        
        if datetime.now() > datetime.fromisoformat(self.password_reset_expires):
            return False
        
        return secrets.compare_digest(self.password_reset_token, token)
    
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if not self.locked_until:
            return False
        return datetime.now() < datetime.fromisoformat(self.locked_until)
    
    def lock_account(self, minutes: int = 30):
        """Lock account for specified minutes."""
        self.locked_until = (datetime.now() + timedelta(minutes=minutes)).isoformat()
        self.failed_login_attempts = 0
    
    def unlock_account(self):
        """Unlock account."""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def record_failed_login(self):
        """Record failed login attempt."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.lock_account()
    
    def record_successful_login(self):
        """Record successful login."""
        self.last_login = datetime.now().isoformat()
        self.failed_login_attempts = 0
        self.unlock_account()
    
    def get_full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        role_permissions = {
            UserRole.ADMIN.value: ['all'],
            UserRole.MANAGER.value: ['read', 'write', 'export', 'backup'],
            UserRole.USER.value: ['read', 'write'],
            UserRole.VIEWER.value: ['read']
        }
        
        user_permissions = role_permissions.get(self.role, [])
        return 'all' in user_permissions or permission in user_permissions
    
    def validate(self) -> bool:
        """Validate user data."""
        if not self.username or len(self.username) < 3:
            return False
        if not self.email or '@' not in self.email:
            return False
        if self.role not in [role.value for role in UserRole]:
            return False
        if self.status not in [status.value for status in UserStatus]:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding sensitive data)."""
        base_dict = super().to_dict()
        base_dict.update({
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'email_verified': self.email_verified,
            'last_login': self.last_login,
            'failed_login_attempts': self.failed_login_attempts,
            'locked_until': self.locked_until,
            'email_verification_token': self.email_verification_token,
            'password_reset_token': self.password_reset_token is not None,
            'password_reset_expires': self.password_reset_expires
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary."""
        user = cls(
            username=data['username'],
            email=data['email'],
            password="",  # Don't hash again, we'll set the hash directly
            role=data.get('role', UserRole.USER.value),
            status=data.get('status', UserStatus.PENDING_VERIFICATION.value),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone=data.get('phone', ''),
            email_verified=data.get('email_verified', False),
            last_login=data.get('last_login'),
            failed_login_attempts=data.get('failed_login_attempts', 0),
            locked_until=data.get('locked_until'),
            id=data.get('id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
        # Set the password hash directly from the database data
        user.password_hash = data.get('password_hash', '')
        # Set tokens directly
        user.email_verification_token = data.get('email_verification_token')
        user.password_reset_token = data.get('password_reset_token')
        user.password_reset_expires = data.get('password_reset_expires')
        return user
    
    def __str__(self) -> str:
        return f"User({self.username}, {self.email})"

class UserSession:
    """User session management."""
    
    def __init__(self, user_id: str, session_token: str, expires_at: str, 
                 ip_address: str = "", user_agent: str = ""):
        self.user_id = user_id
        self.session_token = session_token
        self.expires_at = expires_at
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = datetime.now().isoformat()
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now() > datetime.fromisoformat(self.expires_at)
    
    def extend_session(self, hours: int = 24):
        """Extend session expiration."""
        self.expires_at = (datetime.now() + timedelta(hours=hours)).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'user_id': self.user_id,
            'session_token': self.session_token,
            'expires_at': self.expires_at,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        """Create session from dictionary."""
        session = cls(
            user_id=data['user_id'],
            session_token=data['session_token'],
            expires_at=data['expires_at'],
            ip_address=data.get('ip_address', ''),
            user_agent=data.get('user_agent', '')
        )
        session.created_at = data.get('created_at', session.created_at)
        return session
