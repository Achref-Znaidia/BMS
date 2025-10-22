"""
Dashboard view component.
"""

import flet as ft
from typing import Dict, Any, Callable
from datetime import datetime
from ...config import ThemeConfig

class DashboardView:
    """Dashboard view for displaying statistics and recent activities."""
    
    def __init__(self, page: ft.Page, get_priority_color: Callable[[str], str]):
        self.page = page
        self.get_priority_color = get_priority_color
    
    def create_dashboard_content(self, dashboard_data: Dict[str, Any]) -> ft.Container:
        """Create dashboard content with statistics and recent activities."""
        stats = dashboard_data['statistics']
        recent_activities = dashboard_data['recent_activities']
        
        # Create statistics cards
        stats_row = ft.Row([
            self._create_stat_card("Pending Handovers", str(stats['pending_handovers']), ft.colors.ORANGE_300),
            self._create_stat_card("Open Issues", str(stats['open_issues']), ft.colors.RED_300),
            self._create_stat_card("Failed Test Suites", str(stats['failed_suites']), ft.colors.PURPLE_300),
            self._create_stat_card("Total Requirements", str(stats['total_requirements']), ft.colors.BLUE_300),
        ], scroll=ft.ScrollMode.ADAPTIVE)
        
        # Create recent activity list
        recent_activity = ft.Column()
        
        for activity in recent_activities:
            recent_activity.controls.append(self._create_activity_item(activity))
        
        if not recent_activities:
            recent_activity.controls.append(
                ft.Text("No recent activities", style="bodyMedium", color=ft.colors.GREY)
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                stats_row,
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=20),
                ft.Text("Recent Activity", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                recent_activity
            ], scroll=ft.ScrollMode.ADAPTIVE),
            padding=20
        )
    
    def _create_stat_card(self, title: str, value: str, color: str) -> ft.Card:
        """Create a statistics card."""
        # Adjust colors for dark mode
        if self.page.theme_mode == ft.ThemeMode.DARK:
            # Make colors slightly darker for dark mode
            if color == ft.colors.ORANGE_300:
                color = ft.colors.ORANGE_700
            elif color == ft.colors.RED_300:
                color = ft.colors.RED_700
            elif color == ft.colors.PURPLE_300:
                color = ft.colors.PURPLE_700
            elif color == ft.colors.BLUE_300:
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
    
    def _create_activity_item(self, activity: Dict[str, Any]) -> ft.ListTile:
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
            color = ft.colors.GREY
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
            trailing=ft.Text(timestamp, size=12, color=ft.colors.GREY),
        )
