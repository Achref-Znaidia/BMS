"""
Business Management System service layer.
Contains business logic and orchestrates data operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models import Handover, Requirement, Issue, TestSuite
from .database import DatabaseManager
from ..config import StatusOptions, PriorityOptions, IssueTypes

class BMSService:
    """Main service class for BMS business logic."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
    
    # Handover operations
    def create_handover(self, from_team: str, to_team: str, date: str, 
                       description: str = "", documents: List[str] = None, 
                       status: str = StatusOptions.HandoverStatus.PENDING.value) -> str:
        """Create a new handover."""
        handover = Handover(
            from_team=from_team,
            to_team=to_team,
            date=date,
            description=description,
            documents=documents or [],
            status=status
        )
        return self.db.add_handover(handover)
    
    def update_handover(self, handover_id: str, **kwargs) -> bool:
        """Update an existing handover."""
        try:
            # Get existing handover data
            handovers = self.db.get_handovers()
            existing_handover = next((h for h in handovers if h.id == handover_id), None)
            
            if not existing_handover:
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(existing_handover, key):
                    setattr(existing_handover, key, value)
            
            self.db.update_handover(handover_id, existing_handover)
            return True
        except Exception:
            return False
    
    def get_handovers(self, status_filter: Optional[str] = None) -> List[Handover]:
        """Get handovers with optional filtering."""
        return self.db.get_handovers(status_filter)
    
    def delete_handover(self, handover_id: str) -> bool:
        """Delete a handover."""
        return self.db.delete_handover(handover_id)
    
    # Requirement operations
    def create_requirement(self, title: str, description: str = "", change_date: str = "",
                          priority: str = PriorityOptions.RequirementPriority.MEDIUM.value,
                          status: str = StatusOptions.RequirementStatus.NEW.value) -> str:
        """Create a new requirement."""
        requirement = Requirement(
            title=title,
            description=description,
            change_date=change_date,
            priority=priority,
            status=status
        )
        return self.db.add_requirement(requirement)
    
    def update_requirement(self, requirement_id: str, **kwargs) -> bool:
        """Update an existing requirement."""
        try:
            # Get existing requirement data
            requirements = self.db.get_requirements()
            existing_requirement = next((r for r in requirements if r.id == requirement_id), None)
            
            if not existing_requirement:
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(existing_requirement, key):
                    setattr(existing_requirement, key, value)
            
            self.db.update_requirement(requirement_id, existing_requirement)
            return True
        except Exception:
            return False
    
    def get_requirements(self, status_filter: Optional[str] = None, 
                        priority_filter: Optional[str] = None) -> List[Requirement]:
        """Get requirements with optional filtering."""
        return self.db.get_requirements(status_filter, priority_filter)
    
    def delete_requirement(self, requirement_id: str) -> bool:
        """Delete a requirement."""
        return self.db.delete_requirement(requirement_id)
    
    # Issue operations
    def create_issue(self, title: str, description: str = "", 
                    issue_type: str = IssueTypes.INFRASTRUCTURE.value,
                    priority: str = PriorityOptions.IssuePriority.MEDIUM.value,
                    status: str = StatusOptions.IssueStatus.OPEN.value,
                    assigned_to: str = "Unassigned") -> str:
        """Create a new issue."""
        issue = Issue(
            title=title,
            description=description,
            type=issue_type,
            priority=priority,
            status=status,
            assigned_to=assigned_to
        )
        return self.db.add_issue(issue)
    
    def update_issue(self, issue_id: str, **kwargs) -> bool:
        """Update an existing issue."""
        try:
            # Get existing issue data
            issues = self.db.get_issues()
            existing_issue = next((i for i in issues if i.id == issue_id), None)
            
            if not existing_issue:
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(existing_issue, key):
                    setattr(existing_issue, key, value)
            
            self.db.update_issue(issue_id, existing_issue)
            return True
        except Exception:
            return False
    
    def get_issues(self, type_filter: Optional[str] = None,
                  status_filter: Optional[str] = None,
                  priority_filter: Optional[str] = None) -> List[Issue]:
        """Get issues with optional filtering."""
        return self.db.get_issues(type_filter, status_filter, priority_filter)
    
    def delete_issue(self, issue_id: str) -> bool:
        """Delete an issue."""
        return self.db.delete_issue(issue_id)
    
    # Test Suite operations
    def create_test_suite(self, name: str, last_run: str = "",
                         status: str = StatusOptions.TestSuiteStatus.NOT_RUN.value,
                         failures: int = 0, fix_notes: str = "") -> str:
        """Create a new test suite."""
        test_suite = TestSuite(
            name=name,
            last_run=last_run,
            status=status,
            failures=failures,
            fix_notes=fix_notes
        )
        return self.db.add_test_suite(test_suite)
    
    def update_test_suite(self, test_suite_id: str, **kwargs) -> bool:
        """Update an existing test suite."""
        try:
            # Get existing test suite data
            test_suites = self.db.get_test_suites()
            existing_test_suite = next((ts for ts in test_suites if ts.id == test_suite_id), None)
            
            if not existing_test_suite:
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(existing_test_suite, key):
                    setattr(existing_test_suite, key, value)
            
            self.db.update_test_suite(test_suite_id, existing_test_suite)
            return True
        except Exception:
            return False
    
    def get_test_suites(self, status_filter: Optional[str] = None) -> List[TestSuite]:
        """Get test suites with optional filtering."""
        return self.db.get_test_suites(status_filter)
    
    def delete_test_suite(self, test_suite_id: str) -> bool:
        """Delete a test suite."""
        return self.db.delete_test_suite(test_suite_id)
    
    def rerun_test_suite(self, test_suite_id: str) -> bool:
        """Re-run a test suite (simulate)."""
        return self.update_test_suite(
            test_suite_id,
            last_run=datetime.now().strftime("%Y-%m-%d"),
            status=StatusOptions.TestSuiteStatus.RUNNING.value
        )
    
    # Dashboard operations
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard statistics and recent activities."""
        all_handovers = self.db.get_handovers()
        all_requirements = self.db.get_requirements()
        all_issues = self.db.get_issues()
        all_test_suites = self.db.get_test_suites()
        recent_activities = self.db.get_recent_activities(5)
        
        # Calculate statistics
        pending_handovers = len([h for h in all_handovers if h.status == StatusOptions.HandoverStatus.PENDING.value])
        open_issues = len([i for i in all_issues if i.status == StatusOptions.IssueStatus.OPEN.value])
        failed_suites = len([ts for ts in all_test_suites if ts.status == StatusOptions.TestSuiteStatus.FAILED.value])
        total_requirements = len(all_requirements)
        
        return {
            'statistics': {
                'pending_handovers': pending_handovers,
                'open_issues': open_issues,
                'failed_suites': failed_suites,
                'total_requirements': total_requirements
            },
            'recent_activities': recent_activities,
            'all_handovers': [h.to_dict() for h in all_handovers],
            'all_requirements': [r.to_dict() for r in all_requirements],
            'all_issues': [i.to_dict() for i in all_issues],
            'all_test_suites': [ts.to_dict() for ts in all_test_suites]
        }
    
    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get available filter options for UI."""
        return {
            'handover_status': [status.value for status in StatusOptions.HandoverStatus],
            'requirement_status': [status.value for status in StatusOptions.RequirementStatus],
            'requirement_priority': [priority.value for priority in PriorityOptions.RequirementPriority],
            'issue_type': [issue_type.value for issue_type in IssueTypes],
            'issue_status': [status.value for status in StatusOptions.IssueStatus],
            'issue_priority': [priority.value for priority in PriorityOptions.IssuePriority],
            'test_suite_status': [status.value for status in StatusOptions.TestSuiteStatus]
        }
