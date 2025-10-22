"""
Authentication and user management service.
"""

import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import json

from ..models.user import User, UserRole, UserStatus, UserSession
from ..services.email_service import EmailService
from ..config import DatabaseConfig

class AuthService:
    """Service for user authentication and management."""
    
    def __init__(self, db_name: str = DatabaseConfig.DB_NAME, 
                 email_service: EmailService = None):
        """
        Initialize authentication service.
        
        Args:
            db_name: Database file name
            email_service: Email service for notifications
        """
        self.db_name = db_name
        self.email_service = email_service or EmailService()
        self._create_tables()
        self._create_default_admin()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_name)
    
    def _create_tables(self):
        """Create authentication tables."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                email_verified BOOLEAN DEFAULT FALSE,
                last_login TEXT,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TEXT,
                email_verification_token TEXT,
                password_reset_token TEXT,
                password_reset_expires TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Email notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                sent_at TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User notifications table (for inbox)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT DEFAULT 'info',
                read BOOLEAN DEFAULT FALSE,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _create_default_admin(self):
        """Create default admin user if none exists."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (UserRole.ADMIN.value,))
        if cursor.fetchone()[0] == 0:
            admin_user = User(
                username="admin",
                email="admin@bms.local",
                password="admin123",  # Should be changed on first login
                role=UserRole.ADMIN.value,
                status=UserStatus.ACTIVE.value,
                first_name="System",
                last_name="Administrator",
                email_verified=True
            )
            self._save_user(admin_user)
        
        conn.close()
    
    def _save_user(self, user: User):
        """Save user to database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (id, username, email, password_hash, role, status, first_name, last_name, phone,
             email_verified, last_login, failed_login_attempts, locked_until, 
             email_verification_token, password_reset_token, password_reset_expires,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user.id, user.username, user.email, user.password_hash, user.role, user.status,
            user.first_name, user.last_name, user.phone, user.email_verified, user.last_login,
            user.failed_login_attempts, user.locked_until, user.email_verification_token,
            user.password_reset_token, user.password_reset_expires, user.created_at, user.updated_at
        ))
        
        conn.commit()
        conn.close()
    
    def _load_user(self, user_id: str) -> Optional[User]:
        """Load user from database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        user_data = {
            'id': row[0], 'username': row[1], 'email': row[2], 'password_hash': row[3],
            'role': row[4], 'status': row[5], 'first_name': row[6], 'last_name': row[7],
            'phone': row[8], 'email_verified': bool(row[9]), 'last_login': row[10],
            'failed_login_attempts': row[11], 'locked_until': row[12],
            'email_verification_token': row[13], 'password_reset_token': row[14],
            'password_reset_expires': row[15], 'created_at': row[16], 'updated_at': row[17]
        }
        
        return User.from_dict(user_data)
    
    def register_user(self, username: str, email: str, password: str,
                     first_name: str = "", last_name: str = "", phone: str = "",
                     role: str = UserRole.USER.value) -> Tuple[bool, str]:
        """
        Register a new user.
        
        Args:
            username: Username
            email: Email address
            password: Password
            first_name: First name
            last_name: Last name
            phone: Phone number
            role: User role
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if username or email already exists
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                conn.close()
                return False, "Username or email already exists"
            
            conn.close()
            
            # Create new user
            user = User(
                username=username,
                email=email,
                password=password,
                role=role,
                status=UserStatus.PENDING_VERIFICATION.value,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            
            if not user.validate():
                return False, "Invalid user data"
            
            # Save user
            self._save_user(user)
            
            # Send verification email
            if self.email_service:
                verification_url = f"http://localhost:8000/verify?token={user.email_verification_token}"
                self.email_service.send_verification_email(
                    user.email, user.username, user.email_verification_token, verification_url
                )
            
            return True, "User registered successfully. Please check your email for verification."
            
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def verify_email(self, token: str) -> Tuple[bool, str]:
        """
        Verify user email with token.
        
        Args:
            token: Verification token
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE email_verification_token = ?", (token,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False, "Invalid verification token"
            
            user_data = {
                'id': row[0], 'username': row[1], 'email': row[2], 'password_hash': row[3],
                'role': row[4], 'status': row[5], 'first_name': row[6], 'last_name': row[7],
                'phone': row[8], 'email_verified': bool(row[9]), 'last_login': row[10],
                'failed_login_attempts': row[11], 'locked_until': row[12],
                'email_verification_token': row[13], 'password_reset_token': row[14],
                'password_reset_expires': row[15], 'created_at': row[16], 'updated_at': row[17]
            }
            
            user = User.from_dict(user_data)
            user.email_verified = True
            user.status = UserStatus.ACTIVE.value
            user.email_verification_token = None
            user.update_timestamp()
            
            self._save_user(user)
            conn.close()
            
            # Send welcome email
            if self.email_service:
                self.email_service.send_welcome_email(user.email, user.username)
            
            return True, "Email verified successfully. You can now log in."
            
        except Exception as e:
            return False, f"Email verification failed: {str(e)}"
    
    def login(self, username_or_email: str, password: str, 
              ip_address: str = "", user_agent: str = "") -> Tuple[bool, str, Optional[User], Optional[str]]:
        """
        Authenticate user login.
        
        Args:
            username_or_email: Username or email
            password: Password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Tuple of (success, message, user, session_token)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Find user by username or email
            cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", 
                          (username_or_email, username_or_email))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False, "Invalid credentials", None, None
            
            user_data = {
                'id': row[0], 'username': row[1], 'email': row[2], 'password_hash': row[3],
                'role': row[4], 'status': row[5], 'first_name': row[6], 'last_name': row[7],
                'phone': row[8], 'email_verified': bool(row[9]), 'last_login': row[10],
                'failed_login_attempts': row[11], 'locked_until': row[12],
                'email_verification_token': row[13], 'password_reset_token': row[14],
                'password_reset_expires': row[15], 'created_at': row[16], 'updated_at': row[17]
            }
            
            user = User.from_dict(user_data)
            
            # Check if account is locked
            if user.is_locked():
                conn.close()
                return False, "Account is locked due to too many failed login attempts", None, None
            
            # Check if email is verified
            if not user.email_verified:
                conn.close()
                return False, "Please verify your email address before logging in", None, None
            
            # Check if account is active
            if user.status != UserStatus.ACTIVE.value:
                conn.close()
                return False, "Account is not active", None, None
            
            # Verify password
            if not user.verify_password(password):
                user.record_failed_login()
                self._save_user(user)
                conn.close()
                return False, "Invalid credentials", None, None
            
            # Check session limits before creating new session
            if not self.check_session_limits(user.id, max_sessions=5):
                # Optionally terminate oldest session to make room
                self.terminate_oldest_session(user.id)
            
            # Check for suspicious activity
            suspicious_activity = self.detect_suspicious_activity(user.id, ip_address)
            if suspicious_activity.get('suspicious', False):
                # Log suspicious activity but still allow login
                print(f"Suspicious login activity detected for user {user.username}: {suspicious_activity['reasons']}")
                # In a production app, you might want to require additional verification here
            
            # Successful login
            user.record_successful_login()
            self._save_user(user)
            
            # Create session
            session = self._create_session(user.id, ip_address, user_agent)
            
            conn.close()
            return True, "Login successful", user, session.session_token
            
        except Exception as e:
            return False, f"Login failed: {str(e)}", None, None
    
    def _create_session(self, user_id: str, ip_address: str = "", user_agent: str = "") -> UserSession:
        """Create user session."""
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        
        session = UserSession(user_id, session_token, expires_at, ip_address, user_agent)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_sessions 
            (session_token, user_id, expires_at, ip_address, user_agent, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session.session_token, session.user_id, session.expires_at,
            session.ip_address, session.user_agent, session.created_at
        ))
        
        conn.commit()
        conn.close()
        
        return session
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """Validate user session."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.*, u.* FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ?
            ''', (session_token,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(row[2])
            if datetime.now() > expires_at:
                self.logout(session_token)
                return None
            
            # Load user data
            user_data = {
                'id': row[6], 'username': row[7], 'email': row[8], 'password_hash': row[9],
                'role': row[10], 'status': row[11], 'first_name': row[12], 'last_name': row[13],
                'phone': row[14], 'email_verified': bool(row[15]), 'last_login': row[16],
                'failed_login_attempts': row[17], 'locked_until': row[18],
                'email_verification_token': row[19], 'password_reset_token': row[20],
                'password_reset_expires': row[21], 'created_at': row[22], 'updated_at': row[23]
            }
            
            return User.from_dict(user_data)
            
        except Exception as e:
            print(f"Session validation failed: {str(e)}")
            return None
    
    def logout(self, session_token: str):
        """Logout user and invalidate session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
        conn.commit()
        conn.close()
    
    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """Request password reset."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False, "Email not found"
            
            user_data = {
                'id': row[0], 'username': row[1], 'email': row[2], 'password_hash': row[3],
                'role': row[4], 'status': row[5], 'first_name': row[6], 'last_name': row[7],
                'phone': row[8], 'email_verified': bool(row[9]), 'last_login': row[10],
                'failed_login_attempts': row[11], 'locked_until': row[12],
                'email_verification_token': row[13], 'password_reset_token': row[14],
                'password_reset_expires': row[15], 'created_at': row[16], 'updated_at': row[17]
            }
            
            user = User.from_dict(user_data)
            reset_token = user.generate_password_reset_token()
            user.update_timestamp()
            
            self._save_user(user)
            conn.close()
            
            # Send password reset email
            if self.email_service:
                reset_url = f"http://localhost:8000/reset-password?token={reset_token}"
                self.email_service.send_password_reset_email(
                    user.email, user.username, reset_token, reset_url
                )
            
            return True, "Password reset email sent"
            
        except Exception as e:
            return False, f"Password reset request failed: {str(e)}"
    
    def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """Reset password with token."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE password_reset_token = ?", (token,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False, "Invalid reset token"
            
            user_data = {
                'id': row[0], 'username': row[1], 'email': row[2], 'password_hash': row[3],
                'role': row[4], 'status': row[5], 'first_name': row[6], 'last_name': row[7],
                'phone': row[8], 'email_verified': bool(row[9]), 'last_login': row[10],
                'failed_login_attempts': row[11], 'locked_until': row[12],
                'email_verification_token': row[13], 'password_reset_token': row[14],
                'password_reset_expires': row[15], 'created_at': row[16], 'updated_at': row[17]
            }
            
            user = User.from_dict(user_data)
            
            if not user.verify_password_reset_token(token):
                conn.close()
                return False, "Invalid or expired reset token"
            
            user.set_password(new_password)
            user.update_timestamp()
            
            self._save_user(user)
            conn.close()
            
            return True, "Password reset successfully"
            
        except Exception as e:
            return False, f"Password reset failed: {str(e)}"
    
    def get_all_users(self) -> List[User]:
        """Get all users."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            user_data = {
                'id': row[0], 'username': row[1], 'email': row[2], 'password_hash': row[3],
                'role': row[4], 'status': row[5], 'first_name': row[6], 'last_name': row[7],
                'phone': row[8], 'email_verified': bool(row[9]), 'last_login': row[10],
                'failed_login_attempts': row[11], 'locked_until': row[12],
                'email_verification_token': row[13], 'password_reset_token': row[14],
                'password_reset_expires': row[15], 'created_at': row[16], 'updated_at': row[17]
            }
            users.append(User.from_dict(user_data))
        
        return users
    
    def send_notification(self, user_emails: List[str], subject: str, 
                         message: str, notification_type: str = "info") -> bool:
        """Send notification to multiple users."""
        if not self.email_service:
            return False
        
        return self.email_service.send_notification_email(
            user_emails, subject, message, notification_type
        )
    
    def get_user_notifications(self, username: str) -> List[Dict[str, Any]]:
        """Get notifications for a specific user."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user ID first
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                conn.close()
                return []
            
            user_id = user_row[0]
            
            # Get notifications for user from user_notifications table
            cursor.execute('''
                SELECT id, subject, message, notification_type, read, created_at
                FROM user_notifications 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            
            notifications = []
            for row in cursor.fetchall():
                notifications.append({
                    'id': row[0],
                    'subject': row[1],
                    'message': row[2],
                    'type': row[3],
                    'read': bool(row[4]),
                    'timestamp': row[5]
                })
            
            conn.close()
            return notifications
            
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
    
    def mark_notification_read(self, username: str, notification_id: str) -> bool:
        """Mark a notification as read."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user ID first
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                conn.close()
                return False
            
            user_id = user_row[0]
            
            # Mark notification as read
            cursor.execute('''
                UPDATE user_notifications 
                SET read = TRUE 
                WHERE id = ? AND user_id = ?
            ''', (notification_id, user_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
    
    def delete_notification(self, username: str, notification_id: str) -> bool:
        """Delete a notification."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user ID first
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                conn.close()
                return False
            
            user_id = user_row[0]
            
            # Delete notification
            cursor.execute('''
                DELETE FROM user_notifications 
                WHERE id = ? AND user_id = ?
            ''', (notification_id, user_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error deleting notification: {e}")
            return False
    
    def create_user_notification(self, username: str, subject: str, message: str, 
                                notification_type: str = "info") -> bool:
        """Create a notification for a specific user."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user ID first
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                conn.close()
                return False
            
            user_id = user_row[0]
            notification_id = secrets.token_urlsafe(16)
            
            # Create notification
            cursor.execute('''
                INSERT INTO user_notifications 
                (id, user_id, subject, message, notification_type, read, created_at)
                VALUES (?, ?, ?, ?, ?, FALSE, ?)
            ''', (notification_id, user_id, subject, message, notification_type, 
                  datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error creating notification: {e}")
            return False
    
    # Session Management Methods
    def get_user_sessions(self, username: str) -> List[Dict[str, Any]]:
        """Get all sessions for a specific user."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user ID first
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                conn.close()
                return []
            
            user_id = user_row[0]
            
            # Clean expired sessions first
            self._cleanup_expired_sessions()
            
            # Get active sessions for user
            cursor.execute('''
                SELECT session_token, user_id, expires_at, ip_address, user_agent, created_at
                FROM user_sessions 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            
            sessions = []
            for row in cursor.fetchall():
                # Parse and format session data
                try:
                    created_at = datetime.fromisoformat(row[5])
                    expires_at = datetime.fromisoformat(row[2])
                    
                    # Determine device/browser from user agent
                    device_info = self._parse_user_agent(row[4])
                    
                    # Calculate session age
                    age = datetime.now() - created_at
                    
                    sessions.append({
                        'session_token': row[0],
                        'ip_address': row[3] or 'Unknown',
                        'device_info': device_info,
                        'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'age': self._format_time_duration(age),
                        'is_current': False,  # Will be set by caller if needed
                        'location': self._get_location_from_ip(row[3]) if row[3] else 'Unknown'
                    })
                except Exception as e:
                    print(f"Error parsing session: {e}")
                    continue
            
            conn.close()
            return sessions
            
        except Exception as e:
            print(f"Error getting user sessions: {e}")
            return []
    
    def terminate_session(self, session_token: str) -> bool:
        """Terminate a specific session."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
            success = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            print(f"Error terminating session: {e}")
            return False
    
    def terminate_all_user_sessions(self, username: str, except_token: str = None) -> int:
        """Terminate all sessions for a user, optionally except current session."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user ID first
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                conn.close()
                return 0
            
            user_id = user_row[0]
            
            if except_token:
                cursor.execute('''
                    DELETE FROM user_sessions 
                    WHERE user_id = ? AND session_token != ?
                ''', (user_id, except_token))
            else:
                cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
            
            terminated_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return terminated_count
            
        except Exception as e:
            print(f"Error terminating user sessions: {e}")
            return 0
    
    def get_session_count(self, username: str) -> int:
        """Get total number of active sessions for a user."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Clean expired sessions first
            self._cleanup_expired_sessions()
            
            # Get user ID first
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                conn.close()
                return 0
            
            user_id = user_row[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            print(f"Error getting session count: {e}")
            return 0
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions from database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            cursor.execute("DELETE FROM user_sessions WHERE expires_at < ?", (current_time,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error cleaning expired sessions: {e}")
    
    def _parse_user_agent(self, user_agent: str) -> str:
        """Parse user agent string to extract device/browser info."""
        if not user_agent:
            return "Unknown Device"
        
        user_agent = user_agent.lower()
        
        # Browser detection
        if 'firefox' in user_agent:
            browser = 'Firefox'
        elif 'chrome' in user_agent:
            browser = 'Chrome'
        elif 'safari' in user_agent and 'chrome' not in user_agent:
            browser = 'Safari'
        elif 'edge' in user_agent:
            browser = 'Edge'
        elif 'opera' in user_agent:
            browser = 'Opera'
        else:
            browser = 'Unknown Browser'
        
        # OS detection
        if 'windows' in user_agent:
            os = 'Windows'
        elif 'mac' in user_agent:
            os = 'macOS'
        elif 'linux' in user_agent:
            os = 'Linux'
        elif 'android' in user_agent:
            os = 'Android'
        elif 'ios' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent:
            os = 'iOS'
        else:
            os = 'Unknown OS'
        
        return f"{browser} on {os}"
    
    def _get_location_from_ip(self, ip_address: str) -> str:
        """Get approximate location from IP address."""
        # In a real implementation, you would use a GeoIP service
        # For now, just return a placeholder
        if ip_address == '127.0.0.1' or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
            return "Local Network"
        elif ip_address:
            return "External Location"
        else:
            return "Unknown Location"
    
    def _format_time_duration(self, duration: timedelta) -> str:
        """Format time duration in human readable format."""
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds} seconds ago"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = total_seconds // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"
    
    def extend_session(self, session_token: str, hours: int = 24) -> bool:
        """Extend session expiration time."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            new_expires_at = (datetime.now() + timedelta(hours=hours)).isoformat()
            cursor.execute('''
                UPDATE user_sessions 
                SET expires_at = ? 
                WHERE session_token = ?
            ''', (new_expires_at, session_token))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            print(f"Error extending session: {e}")
            return False
    
    # Security Features
    def check_session_limits(self, user_id: str, max_sessions: int = 5) -> bool:
        """Check if user has exceeded maximum allowed concurrent sessions."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Clean expired sessions first
            self._cleanup_expired_sessions()
            
            # Count active sessions for user
            cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE user_id = ?", (user_id,))
            session_count = cursor.fetchone()[0]
            
            conn.close()
            return session_count < max_sessions
            
        except Exception as e:
            print(f"Error checking session limits: {e}")
            return True  # Allow if check fails
    
    def detect_suspicious_activity(self, user_id: str, ip_address: str) -> Dict[str, Any]:
        """Detect potentially suspicious login activity."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get recent sessions for this user
            cursor.execute('''
                SELECT ip_address, created_at 
                FROM user_sessions 
                WHERE user_id = ? AND created_at > datetime('now', '-24 hours')
                ORDER BY created_at DESC
            ''', (user_id,))
            
            recent_sessions = cursor.fetchall()
            conn.close()
            
            if not recent_sessions:
                return {'suspicious': False, 'reasons': []}
            
            suspicious_indicators = []
            
            # Check for multiple IPs in short time
            unique_ips = set(session[0] for session in recent_sessions if session[0])
            if len(unique_ips) > 3:
                suspicious_indicators.append(f"Multiple IP addresses ({len(unique_ips)}) in 24 hours")
            
            # Check for rapid session creation
            if len(recent_sessions) > 10:
                suspicious_indicators.append(f"High number of sessions ({len(recent_sessions)}) in 24 hours")
            
            # Check for geographic anomalies (simplified)
            if ip_address and any(session[0] != ip_address for session in recent_sessions[-3:]):
                suspicious_indicators.append("Different IP address from recent sessions")
            
            return {
                'suspicious': len(suspicious_indicators) > 0,
                'reasons': suspicious_indicators,
                'recent_session_count': len(recent_sessions),
                'unique_ip_count': len(unique_ips)
            }
            
        except Exception as e:
            print(f"Error detecting suspicious activity: {e}")
            return {'suspicious': False, 'reasons': [], 'error': str(e)}
    
    def enforce_session_timeout(self, max_idle_hours: int = 8):
        """Enforce session timeout based on idle time."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Calculate timeout threshold
            timeout_threshold = (datetime.now() - timedelta(hours=max_idle_hours)).isoformat()
            
            # Find sessions that haven't been used recently (simplified - in real app, track last activity)
            cursor.execute('''
                SELECT session_token FROM user_sessions 
                WHERE created_at < ? 
            ''', (timeout_threshold,))
            
            idle_sessions = cursor.fetchall()
            
            # Terminate idle sessions
            for session in idle_sessions:
                cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session[0],))
            
            terminated_count = len(idle_sessions)
            conn.commit()
            conn.close()
            
            return terminated_count
            
        except Exception as e:
            print(f"Error enforcing session timeout: {e}")
            return 0
    
    def get_security_summary(self, username: str) -> Dict[str, Any]:
        """Get security summary for a user."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                return {'error': 'User not found'}
            
            user_id = user_row[0]
            
            # Clean expired sessions
            self._cleanup_expired_sessions()
            
            # Get session statistics
            cursor.execute('''
                SELECT COUNT(*) as total_sessions,
                       COUNT(DISTINCT ip_address) as unique_ips,
                       MIN(created_at) as first_session,
                       MAX(created_at) as latest_session
                FROM user_sessions 
                WHERE user_id = ?
            ''', (user_id,))
            
            stats = cursor.fetchone()
            
            # Get recent activity (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM user_sessions 
                WHERE user_id = ? AND created_at > datetime('now', '-24 hours')
            ''', (user_id,))
            
            recent_sessions = cursor.fetchone()[0]
            
            conn.close()
            
            # Detect suspicious activity
            suspicious_activity = self.detect_suspicious_activity(user_id, "")
            
            return {
                'username': username,
                'total_active_sessions': stats[0] or 0,
                'unique_ip_addresses': stats[1] or 0,
                'first_session_date': stats[2] or 'Never',
                'latest_session_date': stats[3] or 'Never',
                'sessions_last_24h': recent_sessions,
                'suspicious_activity': suspicious_activity,
                'security_score': self._calculate_security_score(stats[0] or 0, stats[1] or 0, suspicious_activity)
            }
            
        except Exception as e:
            print(f"Error getting security summary: {e}")
            return {'error': str(e)}
    
    def _calculate_security_score(self, session_count: int, unique_ips: int, suspicious_activity: Dict) -> Dict[str, Any]:
        """Calculate a simple security score based on session patterns."""
        score = 100  # Start with perfect score
        warnings = []
        
        # Deduct points for high session count
        if session_count > 5:
            score -= min(20, (session_count - 5) * 2)
            warnings.append(f"High number of active sessions ({session_count})")
        
        # Deduct points for multiple IPs
        if unique_ips > 3:
            score -= min(15, (unique_ips - 3) * 3)
            warnings.append(f"Multiple IP addresses ({unique_ips})")
        
        # Deduct points for suspicious activity
        if suspicious_activity.get('suspicious', False):
            score -= 25
            warnings.extend(suspicious_activity.get('reasons', []))
        
        score = max(0, score)  # Don't go below 0
        
        # Determine risk level
        if score >= 90:
            risk_level = 'Low'
        elif score >= 70:
            risk_level = 'Medium'
        elif score >= 50:
            risk_level = 'High'
        else:
            risk_level = 'Critical'
        
        return {
            'score': score,
            'risk_level': risk_level,
            'warnings': warnings
        }
    
    def terminate_oldest_session(self, user_id: str) -> bool:
        """Terminate the oldest session for a user to make room for new session."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Find oldest session for user
            cursor.execute('''
                SELECT session_token FROM user_sessions 
                WHERE user_id = ? 
                ORDER BY created_at ASC 
                LIMIT 1
            ''', (user_id,))
            
            result = cursor.fetchone()
            if result:
                oldest_token = result[0]
                cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (oldest_token,))
                conn.commit()
                success = cursor.rowcount > 0
            else:
                success = False
            
            conn.close()
            return success
            
        except Exception as e:
            print(f"Error terminating oldest session: {e}")
            return False
