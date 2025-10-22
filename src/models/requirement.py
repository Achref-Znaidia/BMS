"""
Requirement model class.
"""

from typing import Dict, Any
from .base import BaseModel
from ..config import StatusOptions, PriorityOptions, ValidationRules

class Requirement(BaseModel):
    """Requirement model representing system requirements."""
    
    def __init__(self, title: str, description: str = "", change_date: str = "", 
                 priority: str = PriorityOptions.RequirementPriority.MEDIUM.value,
                 status: str = StatusOptions.RequirementStatus.NEW.value, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.description = description
        self.change_date = change_date
        self.priority = priority
        self.status = status
    
    def validate(self) -> bool:
        """Validate requirement data."""
        if not self.title or len(self.title) < ValidationRules.MIN_TITLE_LENGTH:
            return False
        if len(self.title) > ValidationRules.MAX_TITLE_LENGTH:
            return False
        if len(self.description) > ValidationRules.MAX_DESCRIPTION_LENGTH:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert requirement to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'title': self.title,
            'description': self.description,
            'change_date': self.change_date,
            'priority': self.priority,
            'status': self.status
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Requirement':
        """Create requirement from dictionary."""
        return cls(
            title=data['title'],
            description=data.get('description', ''),
            change_date=data.get('change_date', ''),
            priority=data.get('priority', PriorityOptions.RequirementPriority.MEDIUM.value),
            status=data.get('status', StatusOptions.RequirementStatus.NEW.value),
            id=data.get('id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __str__(self) -> str:
        return f"Requirement({self.title})"
