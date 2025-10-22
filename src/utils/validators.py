"""
Validation utilities for form inputs and data.
"""

from typing import List, Optional
from ..config import ValidationRules, StatusOptions, PriorityOptions, IssueTypes

class Validators:
    """Collection of validation functions."""
    
    @staticmethod
    def validate_required(value: str, field_name: str) -> Optional[str]:
        """Validate required field."""
        if not value or not value.strip():
            return f"{field_name} is required"
        return None
    
    @staticmethod
    def validate_length(value: str, field_name: str, min_length: int = 1, max_length: int = 200) -> Optional[str]:
        """Validate field length."""
        if len(value) < min_length:
            return f"{field_name} must be at least {min_length} characters"
        if len(value) > max_length:
            return f"{field_name} must be no more than {max_length} characters"
        return None
    
    @staticmethod
    def validate_title(title: str) -> Optional[str]:
        """Validate title field."""
        error = Validators.validate_required(title, "Title")
        if error:
            return error
        
        return Validators.validate_length(
            title, "Title", 
            ValidationRules.MIN_TITLE_LENGTH, 
            ValidationRules.MAX_TITLE_LENGTH
        )
    
    @staticmethod
    def validate_description(description: str) -> Optional[str]:
        """Validate description field."""
        if description and len(description) > ValidationRules.MAX_DESCRIPTION_LENGTH:
            return f"Description must be no more than {ValidationRules.MAX_DESCRIPTION_LENGTH} characters"
        return None
    
    @staticmethod
    def validate_handover_data(data: dict) -> List[str]:
        """Validate handover form data."""
        errors = []
        
        # Validate required fields
        if not data.get('from_team'):
            errors.append("From Team is required")
        if not data.get('to_team'):
            errors.append("To Team is required")
        if not data.get('date'):
            errors.append("Date is required")
        
        # Validate field lengths
        if data.get('from_team') and len(data['from_team']) > ValidationRules.MAX_TITLE_LENGTH:
            errors.append("From Team name is too long")
        if data.get('to_team') and len(data['to_team']) > ValidationRules.MAX_TITLE_LENGTH:
            errors.append("To Team name is too long")
        
        # Validate description
        desc_error = Validators.validate_description(data.get('description', ''))
        if desc_error:
            errors.append(desc_error)
        
        # Validate documents count
        documents = data.get('documents', [])
        if len(documents) > ValidationRules.MAX_DOCUMENTS_COUNT:
            errors.append(f"Too many documents (max {ValidationRules.MAX_DOCUMENTS_COUNT})")
        
        return errors
    
    @staticmethod
    def validate_requirement_data(data: dict) -> List[str]:
        """Validate requirement form data."""
        errors = []
        
        # Validate title
        title_error = Validators.validate_title(data.get('title', ''))
        if title_error:
            errors.append(title_error)
        
        # Validate description
        desc_error = Validators.validate_description(data.get('description', ''))
        if desc_error:
            errors.append(desc_error)
        
        # Validate date
        if not data.get('change_date'):
            errors.append("Change Date is required")
        
        return errors
    
    @staticmethod
    def validate_issue_data(data: dict) -> List[str]:
        """Validate issue form data."""
        errors = []
        
        # Validate title
        title_error = Validators.validate_title(data.get('title', ''))
        if title_error:
            errors.append(title_error)
        
        # Validate description
        desc_error = Validators.validate_description(data.get('description', ''))
        if desc_error:
            errors.append(desc_error)
        
        return errors
    
    @staticmethod
    def validate_test_suite_data(data: dict) -> List[str]:
        """Validate test suite form data."""
        errors = []
        
        # Validate name
        name_error = Validators.validate_title(data.get('name', ''))
        if name_error:
            errors.append(name_error)
        
        # Validate failures count
        try:
            failures = int(data.get('failures', 0))
            if failures < 0:
                errors.append("Failures count cannot be negative")
        except (ValueError, TypeError):
            errors.append("Failures count must be a valid number")
        
        # Validate description
        desc_error = Validators.validate_description(data.get('fix_notes', ''))
        if desc_error:
            errors.append(desc_error)
        
        return errors
    
    @staticmethod
    def validate_status(status: str, valid_statuses: List[str]) -> bool:
        """Validate status value."""
        return status in valid_statuses
    
    @staticmethod
    def validate_priority(priority: str, valid_priorities: List[str]) -> bool:
        """Validate priority value."""
        return priority in valid_priorities
