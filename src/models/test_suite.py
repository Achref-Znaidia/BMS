"""
Test Suite model class.
"""

from typing import Dict, Any
from .base import BaseModel
from ..config import StatusOptions, ValidationRules

class TestSuite(BaseModel):
    """Test Suite model representing test execution results."""
    
    def __init__(self, name: str, last_run: str = "", 
                 status: str = StatusOptions.TestSuiteStatus.NOT_RUN.value,
                 failures: int = 0, fix_notes: str = "", **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.last_run = last_run
        self.status = status
        self.failures = failures
        self.fix_notes = fix_notes
    
    def validate(self) -> bool:
        """Validate test suite data."""
        if not self.name or len(self.name) < ValidationRules.MIN_TITLE_LENGTH:
            return False
        if len(self.name) > ValidationRules.MAX_TITLE_LENGTH:
            return False
        if len(self.fix_notes) > ValidationRules.MAX_DESCRIPTION_LENGTH:
            return False
        if self.failures < 0:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert test suite to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'name': self.name,
            'last_run': self.last_run,
            'status': self.status,
            'failures': self.failures,
            'fix_notes': self.fix_notes
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestSuite':
        """Create test suite from dictionary."""
        return cls(
            name=data['name'],
            last_run=data.get('last_run', ''),
            status=data.get('status', StatusOptions.TestSuiteStatus.NOT_RUN.value),
            failures=data.get('failures', 0),
            fix_notes=data.get('fix_notes', ''),
            id=data.get('id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __str__(self) -> str:
        return f"TestSuite({self.name})"
