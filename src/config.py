"""
Configuration module for BMS application.
Contains all configuration constants and settings.
"""

from enum import Enum
from typing import Dict, List

class DatabaseConfig:
    """Database configuration constants."""
    DB_NAME = "bms_database.db"
    DEFAULT_TIMEOUT = 30

class UIConfig:
    """UI configuration constants."""
    APP_TITLE = "BMS - Big Manager System"
    PAGE_PADDING = 20
    CARD_MARGIN = 10
    STAT_CARD_WIDTH = 140
    STAT_CARD_HEIGHT = 100

class StatusOptions:
    """Status options for different entities."""
    
    class HandoverStatus(Enum):
        PENDING = "Pending"
        IN_PROGRESS = "In Progress"
        COMPLETED = "Completed"
        BLOCKED = "Blocked"
    
    class RequirementStatus(Enum):
        NEW = "New"
        IN_REVIEW = "In Review"
        APPROVED = "Approved"
        REJECTED = "Rejected"
        IMPLEMENTED = "Implemented"
    
    class IssueStatus(Enum):
        OPEN = "Open"
        IN_PROGRESS = "In Progress"
        RESOLVED = "Resolved"
        CLOSED = "Closed"
    
    class TestSuiteStatus(Enum):
        NOT_RUN = "Not Run"
        RUNNING = "Running"
        PASSED = "Passed"
        FAILED = "Failed"
        PARTIAL = "Partial"

class PriorityOptions:
    """Priority options for different entities."""
    
    class RequirementPriority(Enum):
        HIGH = "High"
        MEDIUM = "Medium"
        LOW = "Low"
    
    class IssuePriority(Enum):
        CRITICAL = "Critical"
        HIGH = "High"
        MEDIUM = "Medium"
        LOW = "Low"

class IssueTypes(Enum):
    """Issue type options."""
    INFRASTRUCTURE = "Infrastructure"
    TEST_ENVIRONMENT = "Test Environment"
    APPLICATION = "Application"
    PERFORMANCE = "Performance"
    SECURITY = "Security"

class ExportConfig:
    """Export configuration constants."""
    CSV_ENCODING = 'utf-8'
    EXPORT_DATE_FORMAT = '%Y%m%d_%H%M%S'
    DISPLAY_DATE_FORMAT = '%Y-%m-%d %H:%M'

class ThemeConfig:
    """Theme configuration constants."""
    LIGHT_THEME = "light"
    DARK_THEME = "dark"
    
    # Color mappings for different themes
    PRIORITY_COLORS = {
        'light': {
            'Critical': '#d32f2f',
            'High': '#f44336',
            'Medium': '#ff9800',
            'Low': '#4caf50'
        },
        'dark': {
            'Critical': '#ef5350',
            'High': '#e57373',
            'Medium': '#ffb74d',
            'Low': '#81c784'
        }
    }
    
    STAT_CARD_COLORS = {
        'light': {
            'orange': '#ffb74d',
            'red': '#e57373',
            'purple': '#ba68c8',
            'blue': '#64b5f6'
        },
        'dark': {
            'orange': '#f57c00',
            'red': '#d32f2f',
            'purple': '#7b1fa2',
            'blue': '#1976d2'
        }
    }

    # Component-specific palette for light/dark modes
    COMPONENT_COLORS = {
        'light': {
            'handovers':    {'bg': '#E8F5E9', 'accent': '#43A047', 'text': '#1B5E20'},
            'requirements': {'bg': '#E3F2FD', 'accent': '#1976D2', 'text': '#0D47A1'},
            'issues':       {'bg': '#FDECEA', 'accent': '#D32F2F', 'text': '#B71C1C'},
            'test_suites':  {'bg': '#FFF3E0', 'accent': '#FB8C00', 'text': '#E65100'},
            'appbar':       {'bg': '#1976D2', 'fg': '#FAFAFA'},
            'card':         {'bg': '#F5F5F5', 'fg': '#212121'},
            'muted_text':   '#607D8B',
        },
        'dark': {
            'handovers':    {'bg': '#1B5E20', 'accent': '#81C784', 'text': '#E8F5E9'},
            'requirements': {'bg': '#0D47A1', 'accent': '#64B5F6', 'text': '#E3F2FD'},
            'issues':       {'bg': '#B71C1C', 'accent': '#EF9A9A', 'text': '#FFEBEE'},
            'test_suites':  {'bg': '#E65100', 'accent': '#FFCC80', 'text': '#FFF3E0'},
            'appbar':       {'bg': '#0D47A1', 'fg': '#FAFAFA'},
            'card':         {'bg': '#263238', 'fg': '#ECEFF1'},
            'muted_text':   '#B0BEC5',
        }
    }

    # Default accent fallback per theme
    DEFAULT_ACCENT = {
        'light': '#90CAF9',
        'dark': '#90CAF9',
    }

class ValidationRules:
    """Validation rules for form inputs."""
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_DOCUMENTS_COUNT = 10

class SecurityConfig:
    """Security configuration constants."""
    # Encryption settings
    DEFAULT_ENCRYPTION_PASSWORD = None  # Set via environment variable
    ENCRYPTION_ALGORITHM = "AES-256-GCM"
    KEY_DERIVATION_ITERATIONS = 100000
    
    # Compression settings
    DEFAULT_COMPRESSION_TYPE = "gzip"
    COMPRESSION_LEVEL = 6  # 1-9, higher = better compression
    ENABLE_COMPRESSION = True
    ENABLE_ENCRYPTION = True
    
    # Backup settings
    BACKUP_RETENTION_DAYS = 30
    BACKUP_COMPRESSION = True
    BACKUP_ENCRYPTION = True
    
    # Data integrity
    ENABLE_CHECKSUMS = True
    VERIFY_INTEGRITY_ON_READ = True
    
    # Security features
    ENABLE_AUDIT_LOG = True
    MAX_LOGIN_ATTEMPTS = 5
    SESSION_TIMEOUT_MINUTES = 30
