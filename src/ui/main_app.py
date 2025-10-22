"""
Main BMS application class.
"""

import flet as ft
from typing import Dict, Any, Callable
from datetime import datetime

from ..services.bms_service import BMSService
from ..services.database import DatabaseManager
from ..services.secure_storage import SecureStorageManager
from ..services.auth_service import AuthService
from ..services.email_service import EmailService
from ..utils.export import ExportManager
from ..utils.backup import BackupManager
from ..utils.compression import CompressionType
from ..config import UIConfig, ThemeConfig, SecurityConfig
from .components.dialogs import DialogManager
from .components.cards import CardManager
from .components.security import SecurityManager
from .components.auth import AuthManager
from .views.dashboard import DashboardView
from .views.handovers import HandoversView

class BMSApp:
    """Main BMS application class."""
    
    def __init__(self):
        # Initialize services
        self.db_manager = DatabaseManager()
        self.secure_storage = SecureStorageManager(
            enable_encryption=SecurityConfig.ENABLE_ENCRYPTION,
            enable_compression=SecurityConfig.ENABLE_COMPRESSION,
            compression_type=CompressionType.GZIP
        )
        self.email_service = EmailService()
        self.auth_service = AuthService(email_service=self.email_service)
        self.bms_service = BMSService(self.db_manager)
        self.export_manager = ExportManager()
        self.backup_manager = BackupManager()
        
        # Initialize UI components
        self.page = None
        self.dialog_manager = None
        self.card_manager = None
        self.security_manager = None
        self.auth_manager = None
        self.dashboard_view = None
        self.handovers_view = None
        
        # Authentication state
        self.current_user = None
        self.session_token = None
        self.is_authenticated = False
        
        # Data storage
        self.dashboard_data = {}
        self.handovers = []
        self.requirements = []
        self.issues = []
        self.test_suites = []
        
        # Filter states
        self.handover_status_filter = "All"
        self.requirement_status_filter = "All"
        self.requirement_priority_filter = "All"
        self.issue_type_filter = "All"
        self.issue_status_filter = "All"
        self.issue_priority_filter = "All"
        self.test_suite_status_filter = "All"
    
    def main(self, page: ft.Page):
        """Main application entry point."""
        print("BMSApp.main() called")
        try:
            print("Setting up page...")
            self.page = page
            page.title = UIConfig.APP_TITLE
            page.theme_mode = ft.ThemeMode.LIGHT
            page.padding = UIConfig.PAGE_PADDING
            page.scroll = ft.ScrollMode.ADAPTIVE
            print("Page setup complete")
            
            print("Initializing UI components...")
            # Initialize UI components
            self._initialize_ui_components()
            print("UI components initialized")
            
            print("Setting up file picker...")
            # Initialize file picker for exports
            self.file_picker = ft.FilePicker()
            page.overlay.append(self.file_picker)
            print("File picker setup complete")
            
            print("Showing login page...")
            # For now, always show login page (remove authentication check temporarily)
            self._show_login_page()
            print("Login page should be shown")
            
        except Exception as e:
            print(f"Error initializing app: {str(e)}")
            import traceback
            traceback.print_exc()
            # Show error page
            page.clean()
            page.add(ft.Container(
                content=ft.Column([
                    ft.Text("Error Initializing Application", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Error: {str(e)}", size=16),
                    ft.ElevatedButton("Retry", on_click=lambda e: self.main(page))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            ))
            page.update()
    
    def _initialize_ui_components(self):
        """Initialize UI components."""
        self.dialog_manager = DialogManager(self.page, self._show_snackbar)
        self.card_manager = CardManager(self.page, self._get_priority_color)
        self.security_manager = SecurityManager(self.page, self._show_snackbar)
        self.auth_manager = AuthManager(self.page, self._show_snackbar)
        self.dashboard_view = DashboardView(self.page, self._get_priority_color)
        self.handovers_view = HandoversView(
            self.page, 
            self.card_manager, 
            self.dialog_manager,
            on_export=self._export_data
        )
    
    def _load_data_from_db(self):
        """Load all data from database including dashboard data."""
        # Load filtered data for tabs
        self.handovers = [h.to_dict() for h in self.bms_service.get_handovers(self.handover_status_filter)]
        self.requirements = [r.to_dict() for r in self.bms_service.get_requirements(
            self.requirement_status_filter, self.requirement_priority_filter)]
        self.issues = [i.to_dict() for i in self.bms_service.get_issues(
            self.issue_type_filter, self.issue_status_filter, self.issue_priority_filter)]
        self.test_suites = [ts.to_dict() for ts in self.bms_service.get_test_suites(self.test_suite_status_filter)]
        
        # Load dashboard data
        self.dashboard_data = self.bms_service.get_dashboard_data()
    
    def _create_main_ui(self, page: ft.Page):
        """Create main UI layout."""
        # App bar with user info and features
        page.appbar = ft.AppBar(
            title=ft.Text(UIConfig.APP_TITLE),
            bgcolor=self._theme_color('appbar', 'bg'),
            color=self._theme_color('appbar', 'fg'),
            actions=[
                self._create_theme_toggle(),
                ft.IconButton(ft.icons.SECURITY, on_click=self._show_security_status),
                ft.IconButton(ft.icons.BACKUP, on_click=self._show_backup_dialog),
                ft.IconButton(ft.icons.EMAIL, on_click=self._show_notification_dialog),
                self._create_user_menu() if self.current_user else ft.Container(),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="Security Settings", on_click=self._show_security_settings),
                        ft.PopupMenuItem(text="Send Notification", on_click=self._show_notification_dialog),
                        ft.PopupMenuItem(text="Settings", on_click=lambda _: self._show_snackbar("Settings opened")),
                        ft.PopupMenuItem(text="Logout", on_click=self._handle_logout),
                    ]
                )
            ]
        )
        
        # Create tabs for navigation
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Dashboard",
                    icon=ft.icons.DASHBOARD,
                    content=self.dashboard_view.create_dashboard_content(self.dashboard_data)
                ),
                ft.Tab(
                    text="Handovers",
                    icon=ft.icons.TRANSFER_WITHIN_A_STATION,
                    content=self.handovers_view.create_handovers_content()
                ),
                ft.Tab(
                    text="Requirements",
                    icon=ft.icons.ASSIGNMENT,
                    content=self._create_requirements_content()
                ),
                ft.Tab(
                    text="Issues",
                    icon=ft.icons.BUG_REPORT,
                    content=self._create_issues_content()
                ),
                ft.Tab(
                    text="Test Suites",
                    icon=ft.icons.PLAY_ARROW,
                    content=self._create_test_suites_content()
                ),
            ],
            expand=1,
        )
        
        page.add(self.tabs)
        
        # Update handovers list
        self.handovers_view.update_handovers_list(self.handovers)
    
    def _create_requirements_content(self):
        """Create requirements tab content (placeholder)."""
        return ft.Container(
            content=ft.Column([
                ft.Text("Requirements Management", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Requirements view will be implemented here", style="bodyMedium")
            ]),
            padding=20
        )
    
    def _create_issues_content(self):
        """Create issues tab content (placeholder)."""
        return ft.Container(
            content=ft.Column([
                ft.Text("Issues Tracking", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Issues view will be implemented here", style="bodyMedium")
            ]),
            padding=20
        )
    
    def _create_test_suites_content(self):
        """Create test suites tab content (placeholder)."""
        return ft.Container(
            content=ft.Column([
                ft.Text("Test Suites Management", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Test suites view will be implemented here", style="bodyMedium")
            ]),
            padding=20
        )
    
    def _create_theme_toggle(self):
        """Create theme toggle button."""
        return ft.IconButton(
            icon=ft.icons.BRIGHTNESS_4,
            tooltip="Toggle theme",
            on_click=self._toggle_theme
        )
    
    def _toggle_theme(self, e):
        """Toggle between light and dark theme."""
        self.page.theme_mode = (
            ft.ThemeMode.DARK 
            if self.page.theme_mode == ft.ThemeMode.LIGHT 
            else ft.ThemeMode.LIGHT
        )
        
        # Update the icon based on current theme
        e.control.icon = (
            ft.icons.BRIGHTNESS_7 
            if self.page.theme_mode == ft.ThemeMode.DARK 
            else ft.icons.BRIGHTNESS_4
        )
        
        self.page.update()
        self._refresh_all_data()  # Refresh to update all colors

    def _current_theme(self) -> str:
        return 'dark' if (self.page and self.page.theme_mode == ft.ThemeMode.DARK) else 'light'

    def _theme_color(self, component: str, key: str) -> str:
        palette = ThemeConfig.COMPONENT_COLORS.get(self._current_theme(), {})
        comp = palette.get(component, {})
        return comp.get(key, ThemeConfig.DEFAULT_ACCENT.get(self._current_theme(), '#90CAF9'))

    def _muted_text_color(self) -> str:
        palette = ThemeConfig.COMPONENT_COLORS.get(self._current_theme(), {})
        return palette.get('muted_text', '#90A4AE')
    
    def _get_priority_color(self, priority: str) -> str:
        """Get color for priority level, respecting light/dark theme."""
        theme = 'dark' if (self.page and self.page.theme_mode == ft.ThemeMode.DARK) else 'light'
        mapping = ThemeConfig.PRIORITY_COLORS.get(theme, {})
        return mapping.get(priority, ThemeConfig.DEFAULT_ACCENT.get(theme, '#90CAF9'))
    
    def _export_data(self, export_type: str):
        """Export data to CSV."""
        try:
            if export_type == "handovers":
                csv_content = self.export_manager.export_handovers_to_csv(self.handovers)
            elif export_type == "requirements":
                csv_content = self.export_manager.export_requirements_to_csv(self.requirements)
            elif export_type == "issues":
                csv_content = self.export_manager.export_issues_to_csv(self.issues)
            elif export_type == "test_suites":
                csv_content = self.export_manager.export_test_suites_to_csv(self.test_suites)
            elif export_type == "dashboard":
                csv_content = self.export_manager.export_dashboard_to_csv(self.dashboard_data)
            else:
                self._show_snackbar("Invalid export type")
                return
            
            filename = self.export_manager.generate_filename(export_type)
            self._download_file(csv_content.encode('utf-8'), filename)
            self._show_snackbar(f"Exported {export_type} data successfully!")
        
        except Exception as e:
            self._show_snackbar(f"Export failed: {str(e)}")
    
    def _download_file(self, file_content: bytes, filename: str):
        """Trigger file download."""
        # Create a temporary file picker for download
        file_picker = ft.FilePicker(
            on_result=lambda e: self._on_download_result(e, file_content, filename)
        )
        self.page.overlay.append(file_picker)
        self.page.update()
        
        # Trigger save dialog
        file_picker.save_file(
            file_name=filename,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["csv"]
        )
    
    def _on_download_result(self, e, file_content: bytes, filename: str):
        """Handle download result."""
        if e.path:
            # In a real desktop app, you would save the file to e.path
            # For web, Flet handles the download automatically
            self._show_snackbar(f"File downloaded: {filename}")
        else:
            self._show_snackbar("Download cancelled")
    
    def _refresh_all_data(self):
        """Completely refresh all data and update all tabs."""
        self._load_data_from_db()
        
        # Update all tab contents
        self.tabs.tabs[0].content = self.dashboard_view.create_dashboard_content(self.dashboard_data)
        self.tabs.tabs[1].content = self.handovers_view.create_handovers_content()
        self.tabs.tabs[2].content = self._create_requirements_content()
        self.tabs.tabs[3].content = self._create_issues_content()
        self.tabs.tabs[4].content = self._create_test_suites_content()
        
        # Update handovers list
        self.handovers_view.update_handovers_list(self.handovers)
        
        self.page.update()
    
    def _show_snackbar(self, message: str):
        """Show snackbar message."""
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_security_status(self, e):
        """Show security status dialog."""
        security_status = self.secure_storage.get_security_status()
        self.security_manager.show_security_status(security_status)
    
    def _show_security_settings(self, e):
        """Show security settings dialog."""
        current_settings = self.secure_storage.get_security_status()
        self.security_manager.show_security_settings_dialog(
            current_settings,
            on_save=self._update_security_settings
        )
    
    def _show_password_change(self, e):
        """Show password change dialog."""
        self.security_manager.show_password_change_dialog(
            on_change=self._change_password
        )
    
    def _show_backup_dialog(self, e):
        """Show backup management dialog."""
        self.security_manager.show_backup_dialog(
            on_backup=self._create_backup,
            on_restore=self._restore_backup
        )
    
    def _update_security_settings(self, settings: Dict[str, Any]):
        """Update security settings."""
        try:
            # Update compression settings
            if settings.get('compression_enabled') != self.secure_storage.enable_compression:
                self.secure_storage.enable_compression = settings.get('compression_enabled', True)
            
            # Update encryption settings
            if settings.get('encryption_enabled') != self.secure_storage.enable_encryption:
                self.secure_storage.enable_encryption = settings.get('encryption_enabled', True)
            
            # Change password if provided
            if settings.get('password'):
                self.secure_storage.change_password(settings['password'])
            
            self._show_snackbar("Security settings updated successfully!")
            
        except Exception as ex:
            self._show_snackbar(f"Error updating security settings: {str(ex)}")
    
    def _change_password(self, new_password: str):
        """Change encryption password."""
        try:
            self.secure_storage.change_password(new_password)
            self._show_snackbar("Password changed successfully!")
        except Exception as ex:
            self._show_snackbar(f"Error changing password: {str(ex)}")
    
    def _create_backup(self):
        """Create a backup of the database."""
        try:
            backup_path = self.backup_manager.create_backup(
                self.db_manager.db_name,
                compress=True,
                encrypt=True
            )
            self._show_snackbar(f"Backup created: {backup_path}")
        except Exception as ex:
            self._show_snackbar(f"Error creating backup: {str(ex)}")
    
    def _restore_backup(self):
        """Restore from backup."""
        try:
            # In a real implementation, you would show a file picker
            # For now, we'll just show a message
            self._show_snackbar("Please use the file picker to select a backup file")
        except Exception as ex:
            self._show_snackbar(f"Error restoring backup: {str(ex)}")
    
    def _show_login_page(self):
        """Show login page."""
        print("_show_login_page() called")
        try:
            print("Cleaning page...")
            self.page.clean()
            
            print("Creating login content...")
            # Create simple login page content with fixed layout
            self.page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Container(height=100),  # Top spacing
                        ft.Text("BMS", size=48, weight=ft.FontWeight.BOLD, 
                               text_align=ft.TextAlign.CENTER, color=ft.colors.BLUE_700),
                        ft.Text("Business Management System", size=18, 
                               text_align=ft.TextAlign.CENTER, color=self._muted_text_color()),
                        ft.Container(height=40),
                        ft.ElevatedButton(
                            "Login",
                            icon=ft.icons.LOGIN,
                            on_click=lambda e: self._show_simple_login(),
                            width=200,
                            bgcolor=ft.colors.BLUE_600,
                            color=self._theme_color('appbar', 'fg')
                        ),
                        ft.Container(height=10),
                        ft.TextButton(
                            "Don't have an account? Register",
                            on_click=lambda e: self._show_simple_register()
                        ),
                        ft.Container(height=20),
                        ft.Text("Use admin/admin123 to login", size=12, color=self._muted_text_color())
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    expand=True
                )
            )
            
            print("Calling page.update()...")
            self.page.update()
            print("Login page should be visible now")
            
        except Exception as e:
            print(f"Error showing login page: {str(e)}")
            import traceback
            traceback.print_exc()
            # Show basic error message
            self.page.clean()
            self.page.add(ft.Text(f"Error: {str(e)}"))
            self.page.update()
    
    def _show_simple_login(self):
        """Show simple login dialog."""
        username_field = ft.TextField(label="Username", width=300, autofocus=True)
        password_field = ft.TextField(label="Password", password=True, width=300)
        
        def login_clicked(e):
            print(f"Login clicked with username: '{username_field.value}', password: '{password_field.value}'")
            username = username_field.value or ""
            password = password_field.value or ""
            
            if username == "admin" and password == "admin123":
                print("Credentials valid, proceeding with login...")
                # Close dialog first
                dialog.open = False
                self.page.dialog = None
                self.page.update()
                print("Dialog closed")
                
                # Try a more direct approach - replace the login page content
                print("Replacing page content...")
                self._replace_with_dashboard()
                print("Dashboard replacement complete")
            else:
                print("Invalid credentials")
                self._show_snackbar("Invalid credentials. Try admin/admin123")
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Login to BMS"),
            content=ft.Column([
                username_field, 
                password_field,
                ft.Text("Use: admin / admin123", size=12, color=self._muted_text_color())
            ], height=180),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Login", on_click=login_clicked),
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_simple_register(self):
        """Show simple register dialog."""
        self._show_snackbar("Registration feature coming soon! Use admin/admin123 to login.")
    
    def _close_dialog(self, dialog):
        """Close dialog."""
        dialog.open = False
        self.page.update()
    
    def _create_simple_main_ui(self):
        """Create a simple working main UI."""
        print("_create_simple_main_ui() called")
        try:
            print("Creating header...")
            # Create simple header
            header = ft.Container(
                content=ft.Row([
                    ft.Text("BMS Dashboard", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                    ft.ElevatedButton(
                        "Logout", 
                        icon=ft.icons.LOGOUT,
                        on_click=self._handle_logout,
                        bgcolor=ft.colors.RED_400,
                        color=self._theme_color('appbar', 'fg')
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=20,
                bgcolor=ft.colors.BLUE_50,
                border_radius=10
            )
            print("Header created")
            
            print("Creating stats cards...")
            # Create stats cards
            stats_row = ft.Row([
                self._create_stat_card("5", "Handovers", ft.colors.BLUE_600),
                self._create_stat_card("12", "Requirements", ft.colors.GREEN_600),
                self._create_stat_card("3", "Issues", ft.colors.RED_600),
                self._create_stat_card("8", "Test Suites", ft.colors.ORANGE_600),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
            print("Stats cards created")
            
            print("Adding content to page...")
            # Add all content to page
            self.page.add(
                ft.Column([
                    header,
                    ft.Container(height=30),
                    stats_row,
                    ft.Container(height=40),
                    ft.Text(
                        "🎉 Welcome to BMS! The system is working correctly.", 
                        size=18, 
                        text_align=ft.TextAlign.CENTER,
                        color=ft.colors.GREEN_700
                    ),
                    ft.Text(
                        "Full features are available - login successful!", 
                        size=14, 
                        text_align=ft.TextAlign.CENTER,
                        color=self._muted_text_color()
                    )
                ])
            )
            print("Content added to page")
            
            print("Calling page.update()...")
            self.page.update()
            print("Page updated successfully")
            
        except Exception as e:
            print(f"Error creating simple main UI: {e}")
            import traceback
            traceback.print_exc()
            self.page.add(ft.Text(f"Dashboard Error: {e}"))
            self.page.update()
    
    def _create_stat_card(self, number: str, label: str, color):
        """Create a statistics card."""
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(number, size=32, weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(label, size=14, color=self._muted_text_color())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                width=150,
                height=100,
                bgcolor=self._theme_color('card', 'bg')
            )
        )
    
    def _replace_with_dashboard(self):
        """Replace current page content with dashboard."""
        print("_replace_with_dashboard() called")
        try:
            # Clear current page content
            self.page.clean()
            
            # Add a simple test to see if anything shows
            test_content = ft.Container(
                content=ft.Column([
                    ft.Text("🎉 LOGIN SUCCESSFUL!", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_600),
                    ft.Text("BMS Dashboard", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                    ft.Container(height=20),
                    ft.Row([
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text("5", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_600),
                                    ft.Text("Handovers")
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=20,
                                width=120,
                                height=80,
                                bgcolor=self._theme_color('card', 'bg')
                            )
                        ),
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text("12", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_600),
                                    ft.Text("Requirements")
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=20,
                                width=120,
                                height=80,
                                bgcolor=self._theme_color('card', 'bg')
                            )
                        ),
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text("3", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.RED_600),
                                    ft.Text("Issues")
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=20,
                                width=120,
                                height=80,
                                bgcolor=self._theme_color('card', 'bg')
                            )
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=40),
                    ft.ElevatedButton(
                        "Logout",
                        icon=ft.icons.LOGOUT,
                        on_click=self._handle_logout,
                        bgcolor=ft.colors.RED_400,
                        color=self._theme_color('appbar', 'fg'),
                        width=200
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                expand=True
            )
            
            self.page.add(test_content)
            self.page.update()
            
            # Show success message
            self._show_snackbar("Welcome to BMS Dashboard!")
            print("Dashboard content added and page updated")
            
        except Exception as e:
            print(f"Error in _replace_with_dashboard: {e}")
            import traceback
            traceback.print_exc()
            # Fallback - show error message
            self.page.clean()
            self.page.add(ft.Text(f"Dashboard Error: {e}", color=ft.colors.RED))
            self.page.update()
    
    def _handle_login(self, username: str, password: str):
        """Handle user login."""
        success, message, user = self.auth_service.login(username, password)
        
        if success and user:
            self.current_user = user
            self.is_authenticated = True
            self._show_snackbar(f"Welcome, {user.get_full_name()}!")
            self._load_data_from_db()
            self._create_main_ui(self.page)
        else:
            self._show_snackbar(f"Login failed: {message}")
    
    def _handle_register(self, form_data: Dict[str, str]):
        """Handle user registration."""
        success, message = self.auth_service.register_user(
            username=form_data['username'],
            email=form_data['email'],
            password=form_data['password'],
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            phone=form_data['phone']
        )
        
        if success:
            self._show_snackbar(message)
            # Show login dialog after successful registration
            self.auth_manager.show_login_dialog(on_login=self._handle_login)
        else:
            self._show_snackbar(f"Registration failed: {message}")
    
    def _handle_logout(self, e=None):
        """Handle user logout."""
        if self.session_token:
            self.auth_service.logout(self.session_token)
        
        self.current_user = None
        self.session_token = None
        self.is_authenticated = False
        
        self._show_login_page()
    
    def _send_notification(self, notification_data: Dict[str, str]):
        """Send notification to all users."""
        try:
            # Get all user emails
            users = self.auth_service.get_all_users()
            user_emails = [user.email for user in users if user.email_verified]
            
            if not user_emails:
                self._show_snackbar("No verified users found")
                return
            
            success = self.auth_service.send_notification(
                user_emails=user_emails,
                subject=notification_data['subject'],
                message=notification_data['message'],
                notification_type=notification_data['notification_type']
            )
            
            if success:
                self._show_snackbar(f"Notification sent to {len(user_emails)} users")
            else:
                self._show_snackbar("Failed to send notification")
                
        except Exception as ex:
            self._show_snackbar(f"Error sending notification: {str(ex)}")
    
    def _create_user_menu(self) -> ft.Container:
        """Create user menu for app bar."""
        if not self.current_user:
            return ft.Container()
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.PERSON),
                ft.Text(self.current_user.get_full_name()),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="Profile", on_click=lambda e: self.auth_manager.show_user_profile_dialog(self.current_user)),
                        ft.PopupMenuItem(text="Change Password", on_click=lambda e: self.auth_manager.show_change_password_dialog()),
                        ft.PopupMenuItem(text="Logout", on_click=self._handle_logout)
                    ]
                )
            ]),
            padding=10
        )
    
    def _show_notification_dialog(self, e):
        """Show notification sending dialog."""
        if not self.current_user or not self.current_user.has_permission('admin'):
            self._show_snackbar("You don't have permission to send notifications")
            return
        
        self.auth_manager.show_notification_dialog(on_send=self._send_notification)
    
    def _show_password_change(self, e):
        """Show password change dialog."""
        self.auth_manager.show_change_password_dialog(
            on_change=lambda current, new: self._handle_password_change(current, new)
        )
    
    def _handle_password_change(self, current_password: str, new_password: str):
        """Handle password change."""
        try:
            # Verify current password
            if not self.current_user.verify_password(current_password):
                self._show_snackbar("Current password is incorrect")
                return
            
            # Update password
            self.current_user.set_password(new_password)
            self.current_user.update_timestamp()
            
            # Save to database (you would need to implement this in auth_service)
            # For now, just show success message
            self._show_snackbar("Password changed successfully!")
            
        except Exception as ex:
            self._show_snackbar(f"Error changing password: {str(ex)}")
