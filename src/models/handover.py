"""
Handover model class.
"""

from typing import List, Dict, Any
from .base import BaseModel
from ..config import StatusOptions, ValidationRules

class Handover(BaseModel):
    """Handover model representing team handovers."""
    
    def __init__(self, from_team: str, to_team: str, date: str, 
                 description: str = "", documents: List[str] = None, 
                 status: str = StatusOptions.HandoverStatus.PENDING.value, **kwargs):
        super().__init__(**kwargs)
        self.from_team = from_team
        self.to_team = to_team
        self.date = date
        self.description = description
        self.documents = documents or []
        self.status = status
    
    def validate(self) -> bool:
        """Validate handover data."""
        if not self.from_team or not self.to_team:
            return False
        if len(self.from_team) > ValidationRules.MAX_TITLE_LENGTH:
            return False
        if len(self.to_team) > ValidationRules.MAX_TITLE_LENGTH:
            return False
        if len(self.description) > ValidationRules.MAX_DESCRIPTION_LENGTH:
            return False
        if len(self.documents) > ValidationRules.MAX_DOCUMENTS_COUNT:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert handover to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'from_team': self.from_team,
            'to_team': self.to_team,
            'date': self.date,
            'description': self.description,
            'documents': self.documents,
            'status': self.status
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Handover':
        """Create handover from dictionary."""
        return cls(
            from_team=data['from_team'],
            to_team=data['to_team'],
            date=data['date'],
            description=data.get('description', ''),
            documents=data.get('documents', []),
            status=data.get('status', StatusOptions.HandoverStatus.PENDING.value),
            id=data.get('id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __str__(self) -> str:
        return f"Handover({self.from_team} → {self.to_team})"
