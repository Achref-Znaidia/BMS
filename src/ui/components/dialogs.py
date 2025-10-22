"""
Dialog components for forms and confirmations.
"""

import flet as ft
from typing import Callable, Dict, Any, List, Optional
from datetime import datetime
from ...config import StatusOptions, PriorityOptions, IssueTypes, ValidationRules
from ...utils.validators import Validators

class DialogManager:
    """Manager for creating and handling dialogs."""
    
    def __init__(self, page: ft.Page, show_snackbar: Callable[[str], None]):
        self.page = page
        self.show_snackbar = show_snackbar
    
    def show_handover_dialog(self, handover_data: Optional[Dict[str, Any]] = None, 
                           on_save: Callable[[Dict[str, Any]], None] = None):
        """Show handover create/edit dialog."""
        is_edit = handover_data is not None
        
        # Form fields
        from_team_field = ft.TextField(
            label="From Team", 
            width=400,
            value=handover_data.get('from_team', '') if is_edit else ''
        )
        to_team_field = ft.TextField(
            label="To Team", 
            width=400,
            value=handover_data.get('to_team', '') if is_edit else ''
        )
        date_field = ft.TextField(
            label="Date", 
            width=400,
            value=handover_data.get('date', datetime.now().strftime("%Y-%m-%d")) if is_edit else datetime.now().strftime("%Y-%m-%d")
        )
        description_field = ft.TextField(
            label="Description", 
            multiline=True, 
            width=400,
            max_lines=3,
            value=handover_data.get('description', '') if is_edit else ''
        )
        documents_field = ft.TextField(
            label="Documents (comma separated)", 
            width=400,
            value=', '.join(handover_data.get('documents', [])) if is_edit else ''
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            width=400,
            options=[ft.dropdown.Option(status.value) for status in StatusOptions.HandoverStatus],
            value=handover_data.get('status', StatusOptions.HandoverStatus.PENDING.value) if is_edit else StatusOptions.HandoverStatus.PENDING.value
        )
        
        def save_handover(e):
            form_data = {
                'from_team': from_team_field.value,
                'to_team': to_team_field.value,
                'date': date_field.value,
                'description': description_field.value,
                'documents': [doc.strip() for doc in documents_field.value.split(',')] if documents_field.value else [],
                'status': status_dropdown.value
            }
            
            # Validate data
            errors = Validators.validate_handover_data(form_data)
            if errors:
                self.show_snackbar("Validation errors: " + "; ".join(errors))
                return
            
            if on_save:
                on_save(form_data)
            self.close_dialog(dialog)
        
        def close_dialog(e):
            self.close_dialog(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Handover" if is_edit else "Add New Handover"),
            content=ft.Column([
                from_team_field,
                to_team_field,
                date_field,
                description_field,
                documents_field,
                status_dropdown
            ], height=400, scroll=ft.ScrollMode.ADAPTIVE),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Save", on_click=save_handover),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_requirement_dialog(self, requirement_data: Optional[Dict[str, Any]] = None,
                              on_save: Callable[[Dict[str, Any]], None] = None):
        """Show requirement create/edit dialog."""
        is_edit = requirement_data is not None
        
        title_field = ft.TextField(
            label="Title", 
            width=400,
            value=requirement_data.get('title', '') if is_edit else ''
        )
        description_field = ft.TextField(
            label="Description", 
            multiline=True, 
            width=400,
            max_lines=3,
            value=requirement_data.get('description', '') if is_edit else ''
        )
        date_field = ft.TextField(
            label="Change Date", 
            width=400,
            value=requirement_data.get('change_date', datetime.now().strftime("%Y-%m-%d")) if is_edit else datetime.now().strftime("%Y-%m-%d")
        )
        priority_dropdown = ft.Dropdown(
            label="Priority",
            width=400,
            options=[ft.dropdown.Option(priority.value) for priority in PriorityOptions.RequirementPriority],
            value=requirement_data.get('priority', PriorityOptions.RequirementPriority.MEDIUM.value) if is_edit else PriorityOptions.RequirementPriority.MEDIUM.value
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            width=400,
            options=[ft.dropdown.Option(status.value) for status in StatusOptions.RequirementStatus],
            value=requirement_data.get('status', StatusOptions.RequirementStatus.NEW.value) if is_edit else StatusOptions.RequirementStatus.NEW.value
        )
        
        def save_requirement(e):
            form_data = {
                'title': title_field.value,
                'description': description_field.value,
                'change_date': date_field.value,
                'priority': priority_dropdown.value,
                'status': status_dropdown.value
            }
            
            # Validate data
            errors = Validators.validate_requirement_data(form_data)
            if errors:
                self.show_snackbar("Validation errors: " + "; ".join(errors))
                return
            
            if on_save:
                on_save(form_data)
            self.close_dialog(dialog)
        
        def close_dialog(e):
            self.close_dialog(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Requirement" if is_edit else "Add New Requirement"),
            content=ft.Column([
                title_field,
                description_field,
                date_field,
                priority_dropdown,
                status_dropdown
            ], height=350, scroll=ft.ScrollMode.ADAPTIVE),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Save", on_click=save_requirement),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_issue_dialog(self, issue_data: Optional[Dict[str, Any]] = None,
                         on_save: Callable[[Dict[str, Any]], None] = None):
        """Show issue create/edit dialog."""
        is_edit = issue_data is not None
        
        title_field = ft.TextField(
            label="Title", 
            width=400,
            value=issue_data.get('title', '') if is_edit else ''
        )
        description_field = ft.TextField(
            label="Description", 
            multiline=True, 
            width=400,
            max_lines=3,
            value=issue_data.get('description', '') if is_edit else ''
        )
        type_dropdown = ft.Dropdown(
            label="Type",
            width=400,
            options=[ft.dropdown.Option(issue_type.value) for issue_type in IssueTypes],
            value=issue_data.get('type', IssueTypes.INFRASTRUCTURE.value) if is_edit else IssueTypes.INFRASTRUCTURE.value
        )
        priority_dropdown = ft.Dropdown(
            label="Priority",
            width=400,
            options=[ft.dropdown.Option(priority.value) for priority in PriorityOptions.IssuePriority],
            value=issue_data.get('priority', PriorityOptions.IssuePriority.MEDIUM.value) if is_edit else PriorityOptions.IssuePriority.MEDIUM.value
        )
        assigned_field = ft.TextField(
            label="Assigned To", 
            width=400,
            value=issue_data.get('assigned_to', 'Unassigned') if is_edit else 'Unassigned'
        )
        
        def save_issue(e):
            form_data = {
                'title': title_field.value,
                'description': description_field.value,
                'type': type_dropdown.value,
                'priority': priority_dropdown.value,
                'assigned_to': assigned_field.value
            }
            
            # Validate data
            errors = Validators.validate_issue_data(form_data)
            if errors:
                self.show_snackbar("Validation errors: " + "; ".join(errors))
                return
            
            if on_save:
                on_save(form_data)
            self.close_dialog(dialog)
        
        def close_dialog(e):
            self.close_dialog(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Issue" if is_edit else "Report New Issue"),
            content=ft.Column([
                title_field,
                description_field,
                type_dropdown,
                priority_dropdown,
                assigned_field
            ], height=350, scroll=ft.ScrollMode.ADAPTIVE),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Save", on_click=save_issue),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_test_suite_dialog(self, test_suite_data: Optional[Dict[str, Any]] = None,
                             on_save: Callable[[Dict[str, Any]], None] = None):
        """Show test suite create/edit dialog."""
        is_edit = test_suite_data is not None
        
        name_field = ft.TextField(
            label="Test Suite Name", 
            width=400,
            value=test_suite_data.get('name', '') if is_edit else ''
        )
        last_run_field = ft.TextField(
            label="Last Run Date", 
            width=400,
            value=test_suite_data.get('last_run', datetime.now().strftime("%Y-%m-%d")) if is_edit else datetime.now().strftime("%Y-%m-%d")
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            width=400,
            options=[ft.dropdown.Option(status.value) for status in StatusOptions.TestSuiteStatus],
            value=test_suite_data.get('status', StatusOptions.TestSuiteStatus.NOT_RUN.value) if is_edit else StatusOptions.TestSuiteStatus.NOT_RUN.value
        )
        failures_field = ft.TextField(
            label="Number of Failures", 
            width=400,
            value=str(test_suite_data.get('failures', 0)) if is_edit else "0",
            keyboard_type=ft.KeyboardType.NUMBER
        )
        fix_notes_field = ft.TextField(
            label="Fix Notes", 
            multiline=True, 
            width=400,
            max_lines=3,
            value=test_suite_data.get('fix_notes', '') if is_edit else ''
        )
        
        def save_test_suite(e):
            form_data = {
                'name': name_field.value,
                'last_run': last_run_field.value,
                'status': status_dropdown.value,
                'failures': int(failures_field.value) if failures_field.value else 0,
                'fix_notes': fix_notes_field.value
            }
            
            # Validate data
            errors = Validators.validate_test_suite_data(form_data)
            if errors:
                self.show_snackbar("Validation errors: " + "; ".join(errors))
                return
            
            if on_save:
                on_save(form_data)
            self.close_dialog(dialog)
        
        def close_dialog(e):
            self.close_dialog(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Test Suite" if is_edit else "Add New Test Suite"),
            content=ft.Column([
                name_field,
                last_run_field,
                status_dropdown,
                failures_field,
                fix_notes_field
            ], height=350, scroll=ft.ScrollMode.ADAPTIVE),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Save", on_click=save_test_suite),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_delete_confirmation(self, item_type: str, item_name: str, 
                               on_confirm: Callable[[], None] = None):
        """Show delete confirmation dialog."""
        def confirm_delete(e):
            if on_confirm:
                on_confirm()
            self.close_dialog(dialog)
        
        def cancel_delete(e):
            self.close_dialog(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete this {item_type}?\n\n{item_name}"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.colors.RED)),
            ],
        )
        
        self.show_dialog(dialog)
    
    def show_dialog(self, dialog: ft.AlertDialog):
        """Show a dialog."""
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def close_dialog(self, dialog: ft.AlertDialog):
        """Close a dialog."""
        dialog.open = False
        self.page.update()
