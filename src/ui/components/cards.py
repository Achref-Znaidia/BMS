"""
Card components for displaying data items.
"""

import flet as ft
from typing import Dict, Any, Callable
from datetime import datetime
from ...config import ThemeConfig

class CardManager:
    """Manager for creating data display cards."""
    
    def __init__(self, page: ft.Page, get_priority_color: Callable[[str], str]):
        self.page = page
        self.get_priority_color = get_priority_color

    def _current_theme(self) -> str:
        return 'dark' if (self.page and self.page.theme_mode == ft.ThemeMode.DARK) else 'light'

    def _palette(self) -> Dict[str, Any]:
        from ...config import ThemeConfig
        return ThemeConfig.COMPONENT_COLORS.get(self._current_theme(), {})

    def _component_bg(self, component: str) -> str:
        p = self._palette()
        return p.get(component, {}).get('bg') or p.get('appbar', {}).get('bg') or '#ECEFF1'

    def _muted_text_color(self) -> str:
        return self._palette().get('muted_text', '#90A4AE')
    
    def create_handover_card(self, handover: Dict[str, Any], 
                           on_edit: Callable[[Dict[str, Any]], None] = None,
                           on_delete: Callable[[Dict[str, Any]], None] = None) -> ft.Card:
        """Create a handover display card."""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text(f"{handover['from_team']} → {handover['to_team']}"),
                        subtitle=ft.Text(handover['description']),
                        trailing=ft.Text(handover['status']),
                    ),
                    ft.Row([
                        ft.Text(f"Date: {handover['date']}", size=12),
                        ft.Text(f"Documents: {len(handover['documents'])}", size=12),
                    ], spacing=20),
                    ft.Row([
                        ft.ElevatedButton(
                            "Edit", 
                            icon=ft.icons.EDIT,
                            on_click=lambda e: on_edit(handover) if on_edit else None
                        ),
                        ft.ElevatedButton(
                            "Delete", 
                            icon=ft.icons.DELETE, 
                            color=ft.colors.RED,
                            width=100,
                            on_click=lambda e: on_delete(handover) if on_delete else None
                        ),
                    ], spacing=5)
                ]),
                padding=10,
                bgcolor=self._component_bg('handovers'),
                border_radius=10
            ),
            margin=10
        )
    
    def create_requirement_card(self, requirement: Dict[str, Any],
                              on_edit: Callable[[Dict[str, Any]], None] = None,
                              on_delete: Callable[[Dict[str, Any]], None] = None) -> ft.Card:
        """Create a requirement display card."""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text(requirement['title']),
                        subtitle=ft.Text(requirement['description']),
                        trailing=ft.Container(
                            content=ft.Text(requirement['priority'], color=ft.colors.WHITE),
                            bgcolor=self.get_priority_color(requirement['priority']),
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            border_radius=5
                        ),
                    ),
                    ft.Row([
                        ft.Text(f"Change Date: {requirement['change_date']}", size=12),
                        ft.Text(f"Status: {requirement['status']}", size=12),
                    ], spacing=20),
                    ft.Row([
                        ft.ElevatedButton(
                            "Edit", 
                            icon=ft.icons.EDIT,
                            on_click=lambda e: on_edit(requirement) if on_edit else None
                        ),
                        ft.ElevatedButton(
                            "Delete", 
                            icon=ft.icons.DELETE, 
                            color=ft.colors.RED,
                            width=100,
                            on_click=lambda e: on_delete(requirement) if on_delete else None
                        ),
                    ], spacing=5)
                ]),
                padding=10,
                bgcolor=self._component_bg('requirements'),
                border_radius=10
            ),
            margin=10
        )
    
    def create_issue_card(self, issue: Dict[str, Any],
                         on_edit: Callable[[Dict[str, Any]], None] = None,
                         on_delete: Callable[[Dict[str, Any]], None] = None) -> ft.Card:
        """Create an issue display card."""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text(issue['title']),
                        subtitle=ft.Text(issue['description']),
                        trailing=ft.Column([
                            ft.Text(issue['status']),
                            ft.Text(issue['priority'], 
                                   color=self.get_priority_color(issue['priority']))
                        ])
                    ),
                    ft.Row([
                        ft.Text(f"Type: {issue['type']}", size=12),
                        ft.Text(f"Assigned: {issue['assigned_to']}", size=12),
                    ], spacing=20),
                    ft.Row([
                        ft.ElevatedButton(
                            "Edit", 
                            icon=ft.icons.EDIT,
                            on_click=lambda e: on_edit(issue) if on_edit else None
                        ),
                        ft.ElevatedButton(
                            "Delete", 
                            icon=ft.icons.DELETE, 
                            color=ft.colors.RED,
                            width=100,
                            on_click=lambda e: on_delete(issue) if on_delete else None
                        ),
                    ], spacing=5)
                ]),
                padding=10,
                bgcolor=self._component_bg('issues'),
                border_radius=10
            ),
            margin=10
        )
    
    def create_test_suite_card(self, test_suite: Dict[str, Any],
                             on_edit: Callable[[Dict[str, Any]], None] = None,
                             on_delete: Callable[[Dict[str, Any]], None] = None,
                             on_rerun: Callable[[Dict[str, Any]], None] = None) -> ft.Card:
        """Create a test suite display card."""
        # Color by status using theme palette
        from ...config import ThemeConfig
        theme = self._current_theme()
        palette = ThemeConfig.COMPONENT_COLORS.get(theme, {})
        status_color = (
            palette.get('test_suites', {}).get('accent', '#FB8C00')
            if test_suite['status'] == 'Passed'
            else palette.get('issues', {}).get('accent', '#D32F2F')
        )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        title=ft.Text(test_suite['name']),
                        subtitle=ft.Text(f"Last Run: {test_suite['last_run']}"),
                        trailing=ft.Column([
                            ft.Text(test_suite['status'], color=status_color),
                            ft.Text(f"Failures: {test_suite['failures']}", 
                                   color=ft.colors.RED if test_suite['failures'] > 0 else ft.colors.GREEN)
                        ])
                    ),
                    ft.Text(f"Fix Notes: {test_suite.get('fix_notes', '')}", size=12) if test_suite.get('fix_notes') else ft.Container(),
                    ft.Row([
                        ft.ElevatedButton(
                            "Re-run", 
                            icon=ft.icons.PLAY_ARROW,
                            on_click=lambda e: on_rerun(test_suite) if on_rerun else None
                        ),
                        ft.ElevatedButton(
                            "Edit", 
                            icon=ft.icons.EDIT,
                            on_click=lambda e: on_edit(test_suite) if on_edit else None
                        ),
                        ft.ElevatedButton(
                            "Delete", 
                            icon=ft.icons.DELETE, 
                            color=ft.colors.RED,
                            width=100,
                            on_click=lambda e: on_delete(test_suite) if on_delete else None
                        ),
                    ], spacing=5)
                ]),
                padding=10,
                bgcolor=self._component_bg('test_suites'),
                border_radius=10
            ),
            margin=10
        )
    
    def create_stat_card(self, title: str, value: str, color: str) -> ft.Card:
        """Create a statistics card for dashboard."""
        # Adjust colors for dark mode
        if self.page.theme_mode == ft.ThemeMode.DARK:
            # Make colors slightly darker for dark mode
            if 'orange' in color.lower():
                color = ft.colors.ORANGE_700
            elif 'red' in color.lower():
                color = ft.colors.RED_700
            elif 'purple' in color.lower():
                color = ft.colors.PURPLE_700
            elif 'blue' in color.lower():
                color = ft.colors.BLUE_700
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=12),
                ], 
                alignment=ft.MainAxisAlignment.CENTER, 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=140,
                height=100,
                padding=10,
                bgcolor=color,
                border_radius=10,
            ),
            margin=5
        )
    
    def create_activity_item(self, activity: Dict[str, Any]) -> ft.ListTile:
        """Create a recent activity list item."""
        # Determine icon and color based on activity type
        if activity['type'] == 'handover':
            icon = ft.icons.TRANSFER_WITHIN_A_STATION
            color = ft.colors.BLUE
            subtitle = f"Handover • {activity.get('description', '')[:50]}..."
        elif activity['type'] == 'requirement':
            icon = ft.icons.ASSIGNMENT
            color = ft.colors.GREEN
            subtitle = f"Requirement • {activity.get('description', '')[:50]}..."
        elif activity['type'] == 'issue':
            icon = ft.icons.BUG_REPORT
            color = ft.colors.RED
            subtitle = f"Issue • {activity.get('description', '')[:50]}..."
        elif activity['type'] == 'test_suite':
            icon = ft.icons.PLAY_ARROW
            color = ft.colors.ORANGE
            subtitle = f"Test Suite • {activity.get('description', '')[:50]}..."
        else:
            icon = ft.icons.INFO
            color = self._muted_text_color()
            subtitle = "Activity"
        
        # Format timestamp
        try:
            timestamp = datetime.fromisoformat(activity['updated_at']).strftime("%Y-%m-%d %H:%M")
        except:
            timestamp = "Recently"
        
        return ft.ListTile(
            title=ft.Text(activity['title']),
            subtitle=ft.Text(subtitle),
            leading=ft.Icon(icon, color=color),
            trailing=ft.Text(timestamp, size=12, color=self._muted_text_color()),
        )
