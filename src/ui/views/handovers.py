"""
Handovers view component.
"""

import flet as ft
from typing import List, Dict, Any, Callable, Optional
from ...config import StatusOptions

class HandoversView:
    """Handovers view for managing team handovers."""
    
    def __init__(self, page: ft.Page, card_manager, dialog_manager, 
                 on_export: Callable[[str], None] = None):
        self.page = page
        self.card_manager = card_manager
        self.dialog_manager = dialog_manager
        self.on_export = on_export
        self.handovers_list = ft.Column(scroll=ft.ScrollMode.ADAPTIVE)
        self.status_filter = "All"
    
    def create_handovers_content(self) -> ft.Container:
        """Create handovers tab content."""
        # Header with add button and export button
        header = ft.Row([
            ft.Text("Team Handovers", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([
                self._create_export_button(),
                ft.Container(width=10),  # Spacing
                ft.ElevatedButton(
                    "New Handover",
                    icon=ft.icons.ADD,
                    on_click=lambda _: self._show_new_handover_dialog()
                )
            ])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Status filter
        status_filter = ft.Dropdown(
            label="Filter by Status",
            width=200,
            options=[ft.dropdown.Option("All")] + [
                ft.dropdown.Option(status.value) for status in StatusOptions.HandoverStatus
            ],
            value=self.status_filter,
            on_change=lambda e: self._apply_filter(e.control.value)
        )
        
        return ft.Container(
            content=ft.Column([
                header,
                ft.Container(height=10),
                status_filter,
                ft.Container(height=20),
                self.handovers_list
            ], scroll=ft.ScrollMode.ADAPTIVE),
            padding=20
        )
    
    def update_handovers_list(self, handovers: List[Dict[str, Any]]):
        """Update the handovers list display."""
        self.handovers_list.controls.clear()
        
        for handover in handovers:
            self.handovers_list.controls.append(
                self.card_manager.create_handover_card(
                    handover,
                    on_edit=self._show_edit_handover_dialog,
                    on_delete=self._show_delete_handover_dialog
                )
            )
        
        if not handovers:
            self.handovers_list.controls.append(
                ft.Text("No handovers found", style="bodyMedium", color=ft.colors.GREY)
            )
        
        self.handovers_list.update()
    
    def _create_export_button(self) -> ft.ElevatedButton:
        """Create export button."""
        return ft.ElevatedButton(
            "Export to CSV",
            icon=ft.icons.DOWNLOAD,
            on_click=lambda _: self.on_export("handovers") if self.on_export else None
        )
    
    def _show_new_handover_dialog(self):
        """Show new handover dialog."""
        self.dialog_manager.show_handover_dialog(
            on_save=self._on_handover_save
        )
    
    def _show_edit_handover_dialog(self, handover: Dict[str, Any]):
        """Show edit handover dialog."""
        self.dialog_manager.show_handover_dialog(
            handover_data=handover,
            on_save=lambda data: self._on_handover_save(data, handover['id'])
        )
    
    def _show_delete_handover_dialog(self, handover: Dict[str, Any]):
        """Show delete handover confirmation."""
        self.dialog_manager.show_delete_confirmation(
            "handover",
            f"{handover['from_team']} → {handover['to_team']}",
            on_confirm=lambda: self._on_handover_delete(handover['id'])
        )
    
    def _apply_filter(self, status_filter: str):
        """Apply status filter."""
        self.status_filter = status_filter
        # This would typically trigger a refresh from the parent component
        # For now, we'll just store the filter value
    
    def _on_handover_save(self, data: Dict[str, Any], handover_id: str = None):
        """Handle handover save."""
        # This would typically call the service layer
        # For now, we'll just show a message
        action = "updated" if handover_id else "added"
        self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Handover {action} successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
    
    def _on_handover_delete(self, handover_id: str):
        """Handle handover delete."""
        # This would typically call the service layer
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Handover deleted successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
