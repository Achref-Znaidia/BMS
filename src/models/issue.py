"""
Issue model class.
"""

from typing import Dict, Any
from .base import BaseModel
from ..config import StatusOptions, PriorityOptions, IssueTypes, ValidationRules

class Issue(BaseModel):
    """Issue model representing system issues."""
    
    def __init__(self, title: str, description: str = "", issue_type: str = IssueTypes.INFRASTRUCTURE.value,
                 priority: str = PriorityOptions.IssuePriority.MEDIUM.value,
                 status: str = StatusOptions.IssueStatus.OPEN.value,
                 assigned_to: str = "Unassigned", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.description = description
        self.type = issue_type
        self.priority = priority
        self.status = status
        self.assigned_to = assigned_to
    
    def validate(self) -> bool:
        """Validate issue data."""
        if not self.title or len(self.title) < ValidationRules.MIN_TITLE_LENGTH:
            return False
        if len(self.title) > ValidationRules.MAX_TITLE_LENGTH:
            return False
        if len(self.description) > ValidationRules.MAX_DESCRIPTION_LENGTH:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'priority': self.priority,
            'status': self.status,
            'assigned_to': self.assigned_to
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Issue':
        """Create issue from dictionary."""
        return cls(
            title=data['title'],
            description=data.get('description', ''),
            issue_type=data.get('type', IssueTypes.INFRASTRUCTURE.value),
            priority=data.get('priority', PriorityOptions.IssuePriority.MEDIUM.value),
            status=data.get('status', StatusOptions.IssueStatus.OPEN.value),
            assigned_to=data.get('assigned_to', 'Unassigned'),
            id=data.get('id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __str__(self) -> str:
        return f"Issue({self.title})"
