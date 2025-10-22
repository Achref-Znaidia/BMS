"""
Export utilities for CSV and other formats.
"""

import csv
import io
from typing import List, Dict, Any
from datetime import datetime
from ..config import ExportConfig

class ExportManager:
    """Manager for data export operations."""
    
    @staticmethod
    def export_handovers_to_csv(handovers: List[Dict[str, Any]]) -> str:
        """Export handovers to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['From Team', 'To Team', 'Date', 'Description', 'Documents', 'Status', 'ID'])
        
        # Write data
        for handover in handovers:
            writer.writerow([
                handover['from_team'],
                handover['to_team'],
                handover['date'],
                handover['description'],
                ', '.join(handover['documents']),
                handover['status'],
                handover['id']
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_requirements_to_csv(requirements: List[Dict[str, Any]]) -> str:
        """Export requirements to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Title', 'Description', 'Change Date', 'Priority', 'Status', 'ID'])
        
        # Write data
        for requirement in requirements:
            writer.writerow([
                requirement['title'],
                requirement['description'],
                requirement['change_date'],
                requirement['priority'],
                requirement['status'],
                requirement['id']
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_issues_to_csv(issues: List[Dict[str, Any]]) -> str:
        """Export issues to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Title', 'Description', 'Type', 'Priority', 'Status', 'Assigned To', 'ID'])
        
        # Write data
        for issue in issues:
            writer.writerow([
                issue['title'],
                issue['description'],
                issue['type'],
                issue['priority'],
                issue['status'],
                issue['assigned_to'],
                issue['id']
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_test_suites_to_csv(test_suites: List[Dict[str, Any]]) -> str:
        """Export test suites to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Name', 'Last Run', 'Status', 'Failures', 'Fix Notes', 'ID'])
        
        # Write data
        for test_suite in test_suites:
            writer.writerow([
                test_suite['name'],
                test_suite['last_run'],
                test_suite['status'],
                test_suite['failures'],
                test_suite.get('fix_notes', ''),
                test_suite['id']
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_dashboard_to_csv(dashboard_data: Dict[str, Any]) -> str:
        """Export dashboard data to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write dashboard statistics
        writer.writerow(['DASHBOARD STATISTICS'])
        writer.writerow(['Metric', 'Count'])
        
        stats = dashboard_data['statistics']
        writer.writerow(['Pending Handovers', stats['pending_handovers']])
        writer.writerow(['Open Issues', stats['open_issues']])
        writer.writerow(['Failed Test Suites', stats['failed_suites']])
        writer.writerow(['Total Requirements', stats['total_requirements']])
        
        writer.writerow([])  # Empty row
        writer.writerow(['RECENT ACTIVITIES'])
        writer.writerow(['Type', 'Title', 'Description', 'Timestamp'])
        
        for activity in dashboard_data['recent_activities']:
            writer.writerow([
                activity['type'],
                activity['title'],
                activity.get('description', '')[:100],  # Limit description length
                activity.get('timestamp', '')
            ])
        
        return output.getvalue()
    
    @staticmethod
    def generate_filename(export_type: str) -> str:
        """Generate filename for export."""
        timestamp = datetime.now().strftime(ExportConfig.EXPORT_DATE_FORMAT)
        return f"{export_type}_export_{timestamp}.csv"
