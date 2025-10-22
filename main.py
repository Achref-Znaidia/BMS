"""
Main entry point for BMS application.
"""

import flet as ft
import asyncio
import sys
import atexit
import os
from datetime import datetime
from src.utils.export import ExportManager
from src.config import ExportConfig
from src.services.secure_database import SecureDatabaseManager
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
from src.models.user import User, UserRole, UserStatus
from src.ui.components.auth import AuthManager

def main(page: ft.Page):
    """Main application entry point."""
    page.title = "BMS - Business Management System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    # Initialize services
    secure_db = SecureDatabaseManager()
    email_service = EmailService()
    auth_service = AuthService(email_service=email_service)
    
    # Initialize authentication manager
    auth_manager = AuthManager(page, lambda msg: show_snackbar(msg))
    
    # Global variables for current user and session
    current_user = None
    current_session_token = None
    
    def show_login():
        """Show login page."""
        page.clean()
        
        # Create login form
        username_field = ft.TextField(
            label="Username or Email", 
            width=300,
            hint_text="Enter username or email",
            autofocus=True
        )
        password_field = ft.TextField(
            label="Password", 
            password=True, 
            width=300,
            hint_text="Enter your password",
            can_reveal_password=True
        )
        
        def login_clicked(e):
            username = username_field.value or ""
            password = password_field.value or ""
            
            if not username or not password:
                show_snackbar("Please enter username and password")
                return
            
            # Authenticate with auth service
            success, message, user, session_token = auth_service.login(
                username, password, 
                ip_address="127.0.0.1",  # In real app, get actual IP
                user_agent="BMS Desktop App"
            )
            
            if success and user and session_token:
                nonlocal current_user, current_session_token
                current_user = user
                current_session_token = session_token
                auth_manager.current_user = user
                auth_manager.session_token = current_session_token
                
                # Add some sample notifications for demo if user has no notifications
                existing_notifications = auth_service.get_user_notifications(user.username)
                if not existing_notifications:
                    auth_service.create_user_notification(
                        username=user.username,
                        subject="Welcome to BMS!",
                        message="Welcome to the Business Management System. You can manage handovers, requirements, issues, and test suites from here.",
                        notification_type="info"
                    )
                    if user.role == "admin":
                        auth_service.create_user_notification(
                            username=user.username,
                            subject="System Update",
                            message="New notification system has been activated. Users can now receive and view notifications in their inbox.",
                            notification_type="update"
                        )
                
                show_main_app()
                # Update notification badge after login
                update_notification_badge()
                # Start periodic notification refresh
                start_notification_refresh()
                show_snackbar(f"Welcome back, {user.get_full_name()}!")
            else:
                show_snackbar(f"Login failed: {message}")
        
        def show_register_dialog():
            """Show registration dialog."""
            def on_register(form_data):
                success, message = auth_service.register_user(
                    username=form_data['username'],
                    email=form_data['email'],
                    password=form_data['password'],
                    first_name=form_data['first_name'],
                    last_name=form_data['last_name'],
                    phone=form_data['phone']
                )
                
                if success:
                    show_snackbar("Registration successful! Please check your email for verification.")
                else:
                    show_snackbar(f"Registration failed: {message}")
            
            auth_manager.show_register_dialog(on_register)
        
        def show_forgot_password_dialog():
            """Show forgot password dialog."""
            def on_reset(email):
                success, message = auth_service.request_password_reset(email)
                if success:
                    show_snackbar("Password reset email sent! Check your inbox.")
                else:
                    show_snackbar(f"Password reset failed: {message}")
            
            auth_manager.show_forgot_password_dialog(on_reset)
        
        # Create login layout with proper spacing
        page.add(
            ft.Column([
                ft.Container(height=30),  # Top spacing
                ft.Text(
                    "BMS", 
                    size=48, 
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.colors.BLUE_700
                ),
                ft.Container(height=10),
                ft.Text(
                    "Business Management System", 
                    size=18, 
                    text_align=ft.TextAlign.CENTER,
                    color=ft.colors.GREY_600
                ),
                ft.Container(height=30),
                
                # Login form centered
                ft.Row([
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Login", size=24, weight=ft.FontWeight.BOLD),
                                ft.Container(height=15),
                                username_field,
                                ft.Container(height=10),
                                password_field,
                                ft.Container(height=20),
                                ft.ElevatedButton(
                                    "Login",
                                    icon=ft.icons.LOGIN,
                                    on_click=login_clicked,
                                    width=300,
                                    bgcolor=ft.colors.BLUE_600,
                                    color=ft.colors.WHITE
                                ),
                                ft.Container(height=10),
                                ft.Row([
                                    ft.TextButton(
                                        "Register",
                                        on_click=lambda e: show_register_dialog()
                                    ),
                                    ft.TextButton(
                                        "Forgot Password?",
                                        on_click=lambda e: show_forgot_password_dialog()
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Container(height=5),
                                ft.Text(
                                    "Default admin: admin / admin123",
                                    size=12,
                                    color=ft.colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER
                                )
                            ], 
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5  # Add spacing between elements
                            ),
                            padding=30,
                            width=400
                        )
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10  # Add spacing between column elements
            )
        )
        page.update()
    
    # Global variables
    main_tabs = None
    
    # Try to load existing data from secure database, otherwise use defaults
    loaded_app_data = secure_db.load_app_data()
    
    if loaded_app_data:
        # Data exists in database, use it
        app_data = loaded_app_data
        # Ensure theme_mode is properly set
        if "theme_mode" in app_data:
            if isinstance(app_data["theme_mode"], str):
                page.theme_mode = ft.ThemeMode.DARK if app_data["theme_mode"] == "DARK" else ft.ThemeMode.LIGHT
            else:
                page.theme_mode = app_data["theme_mode"]
            app_data["theme_mode"] = page.theme_mode
    else:
        # No existing data, use defaults
        app_data = {
            "recent_activities": [],
            "theme_mode": ft.ThemeMode.LIGHT,
            "handovers": [
                {"id": 1, "from_team": "Team Alpha", "to_team": "Team Beta", "description": "Project handover for Q4 deployment", "status": "In Progress", "date": "2024-01-15"},
                {"id": 2, "from_team": "Development", "to_team": "QA", "description": "Feature X testing handover", "status": "Completed", "date": "2024-01-10"}
            ],
            "requirements": [
                {"id": 1, "title": "REQ-001: User Authentication", "description": "Implement secure user login system with 2FA", "priority": "High", "status": "In Development"},
                {"id": 2, "title": "REQ-002: Data Export", "description": "Allow users to export data to CSV/PDF formats", "priority": "Medium", "status": "Completed"}
            ],
            "issues": [
                {"id": 1, "title": "ISS-001: Login Timeout", "description": "Users getting logged out after 5 minutes", "type": "infra", "priority": "Critical", "status": "Open", "assigned": "Backend Team", "assigned_username": None, "created_by": "Admin", "created_by_username": "admin", "created_date": "2024-01-15 09:30:00"},
                {"id": 2, "title": "ISS-002: UI Alignment", "description": "Button alignment issue on mobile devices", "type": "refactor", "priority": "Low", "status": "Resolved", "assigned": "Frontend Team", "assigned_username": None, "created_by": "Admin", "created_by_username": "admin", "created_date": "2024-01-14 14:20:00"}
            ],
            "test_suites": [
                {"id": 1, "name": "Authentication Tests", "type": "Smoke", "status": "Passed", "last_run": "2024-01-15 14:30", "passed": 15, "total": 15, "duration": "2.3s"},
                {"id": 2, "name": "API Integration Tests", "type": "Full", "status": "Failed", "last_run": "2024-01-15 14:25", "passed": 8, "total": 10, "duration": "5.7s"}
            ],
            "benches": [
                {"id": 1, "name": "Development Bench 1", "status": "Available", "assigned_to": "", "project": "", "last_updated": "2024-01-15"},
                {"id": 2, "name": "Testing Bench A", "status": "Occupied", "assigned_to": "QA Team", "project": "Project Alpha", "last_updated": "2024-01-14"}
            ],
            "knowledge_articles": [
                {"id": 1, "title": "How to Setup Development Environment", "content": "Step-by-step guide for setting up the development environment...", "author": "Admin", "created_date": "2024-01-10", "timestamp": "2024-01-10 10:30:00", "tags": ["setup", "development"], "comments": [], "likes": [], "like_count": 0},
                {"id": 2, "title": "Best Practices for Code Review", "content": "Guidelines and best practices for conducting effective code reviews...", "author": "Senior Dev", "created_date": "2024-01-12", "timestamp": "2024-01-12 14:15:00", "tags": ["code-review", "best-practices"], "comments": [], "likes": [], "like_count": 0}
            ],
            "anonymous_proposals": [
                {"id": 1, "title": "Improve CI/CD Pipeline", "description": "Proposal to enhance our CI/CD pipeline for better efficiency...", "status": "Pending Review", "submitted_date": "2024-01-13", "admin_response": "", "response_date": ""}
            ]
        }
    
    # Add some initial demo activities only if no data exists
    if not loaded_app_data or "recent_activities" not in app_data or not app_data["recent_activities"]:
        from datetime import datetime, timedelta
        now = datetime.now()
        app_data["recent_activities"] = [
            {"type": "Test Suite", "description": "Created test suite: Authentication Tests", "timestamp": (now - timedelta(minutes=35)).strftime("%Y-%m-%d %H:%M:%S"), "item_id": 1},
            {"type": "Requirement", "description": "Created requirement: REQ-001: User Authentication", "timestamp": (now - timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S"), "item_id": 1},
            {"type": "Issue", "description": "Reported issue: ISS-001: Login Timeout", "timestamp": (now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"), "item_id": 1},
            {"type": "Handover", "description": "Created handover: Team Alpha → Team Beta", "timestamp": (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"), "item_id": 1}
        ]

    def toggle_theme(e):
        """Toggle between light and dark theme."""
        if app_data["theme_mode"] == ft.ThemeMode.LIGHT:
            app_data["theme_mode"] = ft.ThemeMode.DARK
            page.theme_mode = ft.ThemeMode.DARK
            e.control.icon = ft.icons.BRIGHTNESS_7
        else:
            app_data["theme_mode"] = ft.ThemeMode.LIGHT
            page.theme_mode = ft.ThemeMode.LIGHT
            e.control.icon = ft.icons.BRIGHTNESS_4
        
        # Auto-save theme change
        secure_db.save_app_data(app_data)
        # Refresh all tab contents to apply new theme
        refresh_current_tab()
        show_snackbar("Theme changed successfully!")
    
    def show_snackbar(message: str):
        """Show snackbar message."""
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        page.update()
    
    def check_permission(permission: str) -> bool:
        """Check if current user has permission."""
        if not current_user:
            return False
        return current_user.has_permission(permission)
    
    def require_permission(permission: str):
        """Decorator-like function to check permissions."""
        if not check_permission(permission):
            show_snackbar(f"Access denied. You don't have '{permission}' permission.")
            return False
        return True
    
    def show_user_management_dialog():
        """Show user management dialog for admins."""
        if not require_permission('all'):
            return
        
        users = auth_service.get_all_users()
        
        user_rows = []
        for user in users:
            status_color = {
                'active': ft.colors.GREEN,
                'inactive': ft.colors.GREY,
                'pending_verification': ft.colors.ORANGE,
                'suspended': ft.colors.RED
            }.get(user.status, ft.colors.GREY)
            
            user_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(user.username)),
                        ft.DataCell(ft.Text(user.email)),
                        ft.DataCell(ft.Text(user.get_full_name())),
                        ft.DataCell(ft.Text(user.role.title())),
                        ft.DataCell(ft.Chip(label=ft.Text(user.status.title()), bgcolor=status_color)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    tooltip="Edit User",
                                    on_click=lambda e, u=user: edit_user(u)
                                ),
                                ft.IconButton(
                                    icon=ft.icons.EMAIL,
                                    tooltip="Send Email",
                                    on_click=lambda e, u=user: send_user_email(u)
                                )
                            ])
                        )
                    ]
                )
            )
        
        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Full Name")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=user_rows
        )
        
        def close_dialog(dialog_ref):
            dialog_ref.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("User Management"),
            content=ft.Container(
                content=ft.Column([
                    data_table,
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Send Notification to All",
                        icon=ft.icons.NOTIFICATIONS,
                        on_click=lambda e: (close_dialog(dialog), show_notification_dialog())
                    )
                ]),
                width=800,
                height=500
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: close_dialog(dialog))
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def edit_user(user: User):
        """Edit user details."""
        # Implementation for editing user would go here
        show_snackbar(f"Edit user functionality for {user.username} would be implemented here")
    
    def send_user_email(user: User):
        """Send email to specific user."""
        # Implementation for sending email to user would go here
        show_snackbar(f"Send email functionality for {user.email} would be implemented here")
    
    def show_notification_dialog():
        """Show notification dialog with user selection."""
        if not require_permission('all'):
            return
        
        def on_send(form_data):
            # Get selected users
            selected_user_ids = form_data.get('selected_user_ids', [])
            if not selected_user_ids:
                show_snackbar("No users selected")
                return
            
            # Get all users and filter by selected IDs
            all_users = auth_service.get_all_users()
            selected_users = [user for user in all_users if user.id in selected_user_ids]
            
            if not selected_users:
                show_snackbar("Selected users not found")
                return
            
            # Get emails for selected verified users
            selected_emails = [user.email for user in selected_users if user.email_verified]
            
            # Send email notifications to selected users
            email_success = False
            if selected_emails:
                email_success = auth_service.send_notification(
                    user_emails=selected_emails,
                    subject=form_data['subject'],
                    message=form_data['message'],
                    notification_type=form_data['notification_type']
                )
            
            # Create inbox notifications for selected users
            inbox_success = 0
            for user in selected_users:
                if auth_service.create_user_notification(
                    username=user.username,
                    subject=form_data['subject'],
                    message=form_data['message'],
                    notification_type=form_data['notification_type']
                ):
                    inbox_success += 1
            
            # Show success message
            email_count = len(selected_emails)
            total_users = len(selected_users)
            
            if email_success or inbox_success > 0:
                message_parts = []
                if email_count > 0:
                    message_parts.append(f"{email_count} email{'s' if email_count != 1 else ''}")
                if inbox_success > 0:
                    message_parts.append(f"{inbox_success} inbox{'es' if inbox_success != 1 else ''}")
                
                success_msg = f"Notification sent to {' and '.join(message_parts)}!"
                if total_users != email_count:
                    unverified = total_users - email_count
                    success_msg += f" ({unverified} unverified user{'s' if unverified != 1 else ''} received inbox-only)"
                
                # Update notification badge immediately after sending
                # This ensures badge updates for any user who might have received notifications
                update_notification_badge()
                
                show_snackbar(success_msg)
            else:
                show_snackbar("Failed to send notifications")
        
        # Get all users for the selection dialog
        try:
            users_list = auth_service.get_all_users()
            auth_manager.show_notification_dialog(on_send, users_list)
        except Exception as e:
            show_snackbar(f"Failed to load users: {str(e)}")
            auth_manager.show_notification_dialog(on_send, [])
    
    def logout_user():
        """Logout current user and return to login screen."""
        nonlocal current_user, current_session_token
        
        if current_session_token:
            # Properly terminate the session
            success = auth_service.terminate_session(current_session_token)
            if success:
                show_snackbar("Logged out successfully!")
            else:
                show_snackbar("Logout completed (session cleanup failed)")
            
            # Clean up expired sessions while we're at it
            auth_service._cleanup_expired_sessions()
        
        # Clear local session data
        current_user = None
        current_session_token = None
        auth_manager.current_user = None
        auth_manager.session_token = None
        
        # Return to login screen
        show_login()
    
    def send_notification(e):
        """Send notification to users - updated to use auth system."""
        if not check_permission('all'):
            show_snackbar("Access denied. Admin privileges required.")
            return
        
        show_notification_dialog()
    
    def add_activity(activity_type: str, description: str, item_id: int = None):
        """Add activity to recent activities list."""
        from datetime import datetime
        
        activity = {
            "type": activity_type,
            "description": description,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "item_id": item_id
        }
        
        # Add to beginning of list
        app_data["recent_activities"].insert(0, activity)
        
        # Keep only last 10 activities
        if len(app_data["recent_activities"]) > 10:
            app_data["recent_activities"] = app_data["recent_activities"][:10]
        
        # Auto-save after adding activity
        secure_db.save_app_data(app_data)
    
    def show_export_dialog():
        """Show export dialog with data type selection."""
        def close_dialog(dialog_ref):
            dialog_ref.open = False
            page.update()
        
        def export_selected(e):
            selected_types = []
            if handovers_checkbox.value:
                selected_types.append("Handovers")
            if requirements_checkbox.value:
                selected_types.append("Requirements")
            if issues_checkbox.value:
                selected_types.append("Issues")
            if test_suites_checkbox.value:
                selected_types.append("Test Suites")
            
            if not selected_types:
                show_snackbar("Please select at least one data type to export.")
                return
            
            close_dialog(export_dialog)
            
            # Export each selected type
            for data_type in selected_types:
                export_to_excel(data_type)
        
        handovers_checkbox = ft.Checkbox(label="Handovers", value=True)
        requirements_checkbox = ft.Checkbox(label="Requirements", value=True)
        issues_checkbox = ft.Checkbox(label="Issues", value=True)
        test_suites_checkbox = ft.Checkbox(label="Test Suites", value=True)
        
        export_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Export Data to CSV"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Select data types to export:", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    handovers_checkbox,
                    requirements_checkbox,
                    issues_checkbox,
                    test_suites_checkbox,
                    ft.Container(height=10),
                    ft.Text("Files will be saved to the 'exports' folder.", size=12, color=ft.colors.GREY_600)
                ], spacing=5),
                width=300,
                height=200
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(export_dialog)),
                ft.ElevatedButton(
                    "Export",
                    icon=ft.icons.DOWNLOAD,
                    on_click=export_selected,
                    bgcolor=ft.colors.PURPLE_600,
                    color=ft.colors.WHITE
                )
            ]
        )
        
        page.dialog = export_dialog
        export_dialog.open = True
        page.update()
    
    def export_to_excel(data_type: str):
        """Export data to CSV format using ExportManager."""
        if not require_permission('export'):
            return
        try:
            data = app_data.get(data_type.lower().replace(" ", "_"), [])
            
            if not data:
                show_snackbar(f"⚠️ No {data_type.lower()} data to export!")
                return
            
            # Generate CSV content using ExportManager
            csv_content = None
            if data_type == "Handovers":
                # Map our data structure to match ExportManager expectations
                mapped_data = [{
                    'from_team': h['from_team'],
                    'to_team': h['to_team'], 
                    'date': h['date'],
                    'description': h['description'],
                    'documents': h.get('documents', []),  # Default empty list
                    'status': h['status'],
                    'id': h['id']
                } for h in data]
                csv_content = ExportManager.export_handovers_to_csv(mapped_data)
                
            elif data_type == "Requirements":
                mapped_data = [{
                    'title': r['title'],
                    'description': r['description'],
                    'change_date': r.get('change_date', ''),  # Default empty
                    'priority': r['priority'],
                    'status': r['status'],
                    'id': r['id']
                } for r in data]
                csv_content = ExportManager.export_requirements_to_csv(mapped_data)
                
            elif data_type == "Issues":
                mapped_data = [{
                    'title': i['title'],
                    'description': i['description'],
                    'type': i.get('type', 'General'),  # Default type
                    'priority': i['priority'],
                    'status': i['status'],
                    'assigned_to': i['assigned'],
                    'id': i['id']
                } for i in data]
                csv_content = ExportManager.export_issues_to_csv(mapped_data)
                
            elif data_type == "Test Suites":
                mapped_data = [{
                    'name': ts['name'],
                    'last_run': ts['last_run'],
                    'status': ts['status'],
                    'failures': ts.get('total', 0) - ts.get('passed', 0),  # Calculate failures
                    'fix_notes': ts.get('fix_notes', ''),
                    'id': ts['id']
                } for ts in data]
                csv_content = ExportManager.export_test_suites_to_csv(mapped_data)
            else:
                show_snackbar(f"❌ Unknown data type: {data_type}")
                return
            
            # Create exports directory if it doesn't exist
            exports_dir = os.path.join(os.getcwd(), "exports")
            os.makedirs(exports_dir, exist_ok=True)
            
            # Generate filename using ExportManager
            filename = ExportManager.generate_filename(data_type.lower())
            filepath = os.path.join(exports_dir, filename)
            
            # Write CSV file
            with open(filepath, 'w', encoding=ExportConfig.CSV_ENCODING) as csvfile:
                csvfile.write(csv_content)
            
            show_snackbar(f"✅ {data_type} exported successfully! ({len(data)} records) \nSaved to: exports/{filename}")
            
        except Exception as e:
            show_snackbar(f"❌ Export failed: {str(e)}")
    
    def backup_data(e):
        """Create encrypted and compressed backup of all data."""
        # Check admin permissions for backup operations
        if not current_user or not current_user.has_permission('all'):
            show_snackbar("❌ Access denied. Admin privileges required for backup operations.")
            return
            
        if not require_permission('backup'):
            return
        try:
            # Save current data to database first
            secure_db.save_app_data(app_data)
            
            # Create backup
            backup_path = secure_db.backup_database()
            
            # Get storage stats for the message
            stats = secure_db.get_storage_stats()
            compression_info = ""
            if stats.get('security_features', {}).get('compression_enabled'):
                compression_info = f" (Compressed with {stats['security_features']['compression_type']})"
            
            show_snackbar(f"✅ Encrypted backup created successfully!{compression_info}\nSaved as: {backup_path}")
        except Exception as e:
            show_snackbar(f"❌ Backup failed: {str(e)}")
    
    def restore_database_from_backup(e=None):
        """Restore database from backup - Admin only."""
        # Check admin permissions
        if not current_user or not current_user.has_permission('all'):
            show_snackbar("❌ Access denied. Admin privileges required for database restore.")
            return
        
        def confirm_restore(backup_path):
            def close_dialog(dialog_ref):
                dialog_ref.open = False
                page.update()
            
            def perform_restore(e):
                try:
                    # Restore from backup
                    success = secure_db.restore_database(backup_path)
                    
                    if success:
                        # Close dialog first
                        close_dialog(confirm_dialog)
                        
                        # Reload app data after restore
                        global app_data
                        app_data = secure_db.load_app_data()
                        
                        # Calculate total records for statistics
                        total_records = sum(len(app_data.get(key, [])) for key in ["handovers", "requirements", "issues", "test_suites"])
                        
                        show_snackbar("✅ Database restored successfully! Data loaded.")
                        
                        # Force refresh all tabs with the new data
                        try:
                            global main_tabs
                            if 'main_tabs' in globals():
                                # Update all tab contents with fresh data
                                main_tabs.tabs[0].content = create_dashboard_content()
                                main_tabs.tabs[1].content = create_handovers_content() 
                                main_tabs.tabs[2].content = create_requirements_content()
                                main_tabs.tabs[3].content = create_issues_content()
                                main_tabs.tabs[4].content = create_test_suites_content()
                                
                                # Update user management tab if it exists (for admins)
                                if len(main_tabs.tabs) > 5 and check_permission('all'):
                                    main_tabs.tabs[5].content = create_users_content()
                                
                                # Force page update
                                page.update()
                            else:
                                # Fallback: rebuild main app if tabs not available
                                show_main_app()
                        except Exception as refresh_error:
                            print(f"Refresh error: {refresh_error}")
                            # Fallback refresh
                            refresh_current_tab()
                        
                        # Show updated statistics
                        show_snackbar(f"✅ Import complete! Loaded {total_records} total records.")
                    else:
                        show_snackbar("❌ Database restore failed!")
                        close_dialog(confirm_dialog)
                        
                except Exception as ex:
                    show_snackbar(f"❌ Restore failed: {str(ex)}")
                    close_dialog(confirm_dialog)
            
            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirm Database Restore"),
                content=ft.Column([
                    ft.Icon(ft.icons.WARNING, color=ft.colors.ORANGE, size=48),
                    ft.Text("This will replace ALL current data with the backup data.", 
                            size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("Current data will be permanently lost!", 
                            size=14, color=ft.colors.RED),
                    ft.Text(f"Backup file: {backup_path}", size=12, color=ft.colors.GREY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: close_dialog(confirm_dialog)),
                    ft.ElevatedButton(
                        "Restore Database", 
                        on_click=perform_restore,
                        bgcolor=ft.colors.ORANGE,
                        color=ft.colors.WHITE
                    )
                ]
            )
            
            page.dialog = confirm_dialog
            confirm_dialog.open = True
            page.update()
        
        # Create file picker dialog for backup selection
        def on_file_picked(e: ft.FilePickerResultEvent):
            if e.files and len(e.files) > 0:
                selected_file = e.files[0]
                backup_path = selected_file.path
                show_snackbar(f"📁 Selected backup: {selected_file.name}")
                confirm_restore(backup_path)
            else:
                show_snackbar("❌ No backup file selected")
        
        # Create file picker
        file_picker = ft.FilePicker(on_result=on_file_picked)
        
        # Add file picker to page if not already added
        if file_picker not in page.overlay:
            page.overlay.append(file_picker)
            page.update()
        
        # Open file picker with backup file filters, starting in backups folder
        file_picker.pick_files(
            dialog_title="Select Backup File to Restore",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["bms", "db", "backup"],
            initial_directory="backups"  # Start in backups folder
        )
    
    def clear_database(e=None):
        """Clear all database data - Admin only."""
        # Check admin permissions
        if not current_user or not current_user.has_permission('all'):
            show_snackbar("❌ Access denied. Admin privileges required to clear database.")
            return
        
        def close_dialog(dialog_ref):
            dialog_ref.open = False
            page.update()
        
        def confirm_clear(e):
            try:
                # Clear all data
                success = secure_db.clear_all_data()
                
                if success:
                    # Close dialog first
                    close_dialog(clear_dialog)
                    
                    # Reset app data
                    global app_data
                    
                    # Get current theme mode safely
                    current_theme = ft.ThemeMode.LIGHT
                    try:
                        if 'app_data' in globals() and app_data and isinstance(app_data, dict):
                            current_theme = app_data.get("theme_mode", ft.ThemeMode.LIGHT)
                    except (NameError, AttributeError):
                        current_theme = ft.ThemeMode.LIGHT
                    
                    # Create completely empty data structure
                    empty_data = {
                        "handovers": [],
                        "requirements": [],
                        "issues": [],
                        "test_suites": [],
                        "benches": [],
                        "knowledge_articles": [],
                        "anonymous_proposals": [],
                        "recent_activities": [],
                        "theme_mode": current_theme
                    }
                    
                    # Update the global app_data
                    app_data = empty_data
                    
                    # Force save the empty data multiple times to ensure persistence
                    secure_db.save_app_data(app_data)
                    
                    # Clear the database again to make sure
                    secure_db.clear_all_data()
                    
                    # Save empty data again after clearing
                    secure_db.save_app_data(app_data)
                    
                    show_snackbar("✅ Database emptied successfully! Rebuilding interface...")
                    
                    # Complete application rebuild
                    page.clean()  # Clear everything
                    show_main_app()  # Rebuild from scratch
                    
                    # Final confirmation
                    show_snackbar("✅ All records cleared. Database is now empty.")
                else:
                    show_snackbar("❌ Failed to clear database!")
                    close_dialog(clear_dialog)
                    
            except Exception as ex:
                show_snackbar(f"❌ Clear failed: {str(ex)}")
                close_dialog(clear_dialog)
        
        clear_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ Empty Database"),
            content=ft.Column([
                ft.Icon(ft.icons.DELETE_FOREVER, color=ft.colors.RED, size=48),
                ft.Text("This will permanently delete ALL data!", 
                        size=16, weight=ft.FontWeight.BOLD, color=ft.colors.RED),
                ft.Text("• All handovers, requirements, issues, and test suites\n"
                       "• All user activities and history\n"
                       "• This action cannot be undone!", 
                        size=14),
                ft.Text("Make sure you have a backup before proceeding.", 
                       size=12, color=ft.colors.ORANGE, weight=ft.FontWeight.BOLD),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(clear_dialog)),
                ft.ElevatedButton(
                    "Clear All Data", 
                    on_click=confirm_clear,
                    bgcolor=ft.colors.RED,
                    color=ft.colors.WHITE
                )
            ]
        )
        
        page.dialog = clear_dialog
        clear_dialog.open = True
        page.update()
    
    def show_notifications_inbox():
        """Show user's notifications inbox."""
        # Update badge before showing (in case new notifications arrived)
        update_notification_badge()
        
        # Get notifications for current user
        notifications = auth_service.get_user_notifications(current_user.username)
        
        # Create notification items list
        notification_items = []
        
        if not notifications:
            notification_items.append(
                ft.Container(
                    content=ft.Text("No notifications", 
                                   color=ft.colors.WHITE70 if page.theme_mode == ft.ThemeMode.DARK else ft.colors.GREY, 
                                   text_align=ft.TextAlign.CENTER),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
        else:
            for notification in notifications:
                # Format timestamp
                try:
                    timestamp = notification.get('timestamp', '')
                    if timestamp:
                        # Parse ISO format and show in readable format
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        formatted_time = 'Unknown'
                except:
                    formatted_time = notification.get('timestamp', 'Unknown')
                
                # Use different colors for dark/light mode
                if not notification.get('read', False):
                    card_color = ft.colors.BLUE_900 if page.theme_mode == ft.ThemeMode.DARK else ft.colors.BLUE_50
                else:
                    card_color = ft.colors.GREY_800 if page.theme_mode == ft.ThemeMode.DARK else None
                
                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(
                                    notification.get('subject', 'Notification'), 
                                    weight=ft.FontWeight.BOLD,
                                    size=16
                                ),
                                ft.Text(
                                    formatted_time,
                                    size=12,
                                    color=ft.colors.WHITE60 if page.theme_mode == ft.ThemeMode.DARK else ft.colors.GREY
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Container(height=5),
                            ft.Text(notification.get('message', ''), size=14),
                            ft.Container(height=10),
                            ft.Row([
                                ft.TextButton(
                                    "Mark as Read",
                                    on_click=lambda e, nid=notification.get('id'): mark_notification_read(nid)
                                ) if not notification.get('read', False) else ft.Container(),
                                ft.TextButton(
                                    "Delete",
                                    on_click=lambda e, nid=notification.get('id'): delete_notification(nid),
                                    style=ft.ButtonStyle(color=ft.colors.RED)
                                )
                            ], alignment=ft.MainAxisAlignment.END)
                        ]),
                        padding=15,
                        bgcolor=card_color
                    ),
                    elevation=2 if not notification.get('read', False) else 1,
                    margin=ft.margin.only(bottom=10)
                )
                notification_items.append(card)
        
        # Create scrollable notification list
        notification_list = ft.Column([
            ft.Container(
                content=ft.Text("Your Notifications", size=20, weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(bottom=10)
            ),
            ft.Divider(),
            ft.Container(
                content=ft.ListView(
                    controls=notification_items,
                    expand=True,
                    spacing=5,
                    padding=ft.padding.only(top=10)
                ),
                height=300,  # Fixed height for scrollable area
                expand=True
            )
        ])
        
        def close_notifications_dialog():
            notifications_dialog.open = False
            page.update()
        
        notifications_dialog = ft.AlertDialog(
            title=ft.Text("Notifications"),
            content=ft.Container(
                content=notification_list,
                width=500,
                height=400,
                padding=10
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: close_notifications_dialog())
            ]
        )
        page.dialog = notifications_dialog
        notifications_dialog.open = True
        page.update()
    
    def mark_notification_read(notification_id):
        """Mark notification as read."""
        if auth_service.mark_notification_read(current_user.username, notification_id):
            show_snackbar("Notification marked as read")
            # Close and reopen dialog to refresh content
            if page.dialog:
                page.dialog.open = False
                page.update()
            # Update notification badge
            update_notification_badge()
            show_notifications_inbox()  # Refresh the dialog
        else:
            show_snackbar("Failed to mark notification as read")
        
    def delete_notification(notification_id):
        """Delete notification."""
        if auth_service.delete_notification(current_user.username, notification_id):
            show_snackbar("Notification deleted")
            # Close and reopen dialog to refresh content
            if page.dialog:
                page.dialog.open = False
                page.update()
            # Update notification badge
            update_notification_badge()
            show_notifications_inbox()  # Refresh the dialog
        else:
            show_snackbar("Failed to delete notification")
    
    def get_unread_notification_count():
        """Get count of unread notifications for current user."""
        if not current_user:
            return 0
        try:
            notifications = auth_service.get_user_notifications(current_user.username)
            return len([n for n in notifications if not n.get('read', False)])
        except Exception as e:
            print(f"Error getting notification count: {e}")
            return 0
    
    def create_notification_button():
        """Create notification button with badge showing unread count."""
        unread_count = get_unread_notification_count()
        
        if unread_count > 0:
            # Create badge text
            badge_text = str(unread_count) if unread_count < 100 else "99+"
            
            # Create a better positioned badge that doesn't hide the icon
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.IconButton(
                            ft.icons.NOTIFICATIONS,
                            tooltip=f"View notifications ({unread_count} unread)",
                            on_click=lambda e: show_notifications_inbox()
                        ),
                        ft.Container(
                            content=ft.Text(
                                badge_text,
                                size=8,
                                color=ft.colors.WHITE,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            bgcolor=ft.colors.RED_600,
                            border_radius=7,
                            padding=ft.padding.symmetric(horizontal=2, vertical=1),
                            width=16,
                            height=16,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(left=-20, top=-5)  # Position as top-right badge
                        )
                    ], 
                    spacing=0, 
                    alignment=ft.MainAxisAlignment.START
                    )
                ], 
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER
                ),
                width=48,
                height=48,
                alignment=ft.alignment.center
            )
        else:
            return ft.IconButton(
                ft.icons.NOTIFICATIONS,
                tooltip="View notifications",
                on_click=lambda e: show_notifications_inbox()
            )
    
    def update_notification_badge():
        """Update the notification badge in the app bar."""
        if not current_user or not hasattr(page, 'appbar') or not page.appbar:
            return
        
        try:
            # Find and update the notification button in the app bar
            notification_button_index = None
            
            for i, action in enumerate(page.appbar.actions):
                # More specific identification of notification button
                is_notification_button = False
                
                # Check if it's a single IconButton with notifications icon
                if isinstance(action, ft.IconButton) and action.icon == ft.icons.NOTIFICATIONS:
                    is_notification_button = True
                
                # Check if it's a Row containing our notification button with badge
                elif isinstance(action, ft.Row) and len(action.controls) >= 1:
                    first_control = action.controls[0]
                    if isinstance(first_control, ft.IconButton) and first_control.icon == ft.icons.NOTIFICATIONS:
                        is_notification_button = True
                
                # Check if it's a Container with Row containing notification button (new format)
                elif isinstance(action, ft.Container) and hasattr(action, 'content') and isinstance(action.content, ft.Row):
                    row_controls = action.content.controls
                    if len(row_controls) >= 1 and isinstance(row_controls[0], ft.IconButton) and row_controls[0].icon == ft.icons.NOTIFICATIONS:
                        is_notification_button = True
                
                if is_notification_button:
                    notification_button_index = i
                    break
            
            # Replace the found notification button
            if notification_button_index is not None:
                page.appbar.actions[notification_button_index] = create_notification_button()
                page.update()
                
        except Exception as e:
            print(f"Error updating notification badge: {e}")
    
    def start_notification_refresh():
        """Start periodic notification badge refresh."""
        import threading
        import time
        
        def refresh_loop():
            while current_user is not None:
                try:
                    # Wait 10 seconds between refreshes (more responsive)
                    time.sleep(10)
                    if current_user is not None:
                        update_notification_badge()
                except Exception as e:
                    print(f"Error in notification refresh loop: {e}")
                    break
        
        # Start refresh thread
        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()
    
    def force_badge_refresh():
        """Force immediate badge refresh - useful for testing or manual refresh."""
        try:
            update_notification_badge()
            print("Notification badge refreshed")
        except Exception as e:
            print(f"Error forcing badge refresh: {e}")
    
    def show_storage_stats(e):
        """Show storage statistics and security information."""
        try:
            stats = secure_db.get_storage_stats()
            security_features = stats.get('security_features', {})
            
            message = f"ℹ️ Storage & Security Stats:\n"
            message += f"Database Size: {stats.get('database_file_size_mb', 0)} MB\n"
            message += f"Total Records: {stats.get('total_records', 0)}\n"
            message += f"Encryption: {'Enabled' if security_features.get('encryption_enabled') else 'Disabled'}\n"
            message += f"Compression: {security_features.get('compression_type', 'None')} "
            message += f"({'Enabled' if security_features.get('compression_enabled') else 'Disabled'})\n"
            message += f"Data Integrity: {'Enabled' if security_features.get('checksums_enabled') else 'Disabled'}"
            
            show_snackbar(message)
        except Exception as e:
            show_snackbar(f"❌ Error getting storage stats: {str(e)}")
    
    def show_settings_dialog(e):
        """Show settings configuration dialog with toggleable security features."""
        try:
            # Try to get stats, but handle errors gracefully
            try:
                stats = secure_db.get_storage_stats()
                security_features = stats.get('security_features', {})
                table_stats = stats.get('table_statistics', {})
                # Get current actual configuration from secure_db
                current_config = secure_db.get_current_security_config()
                security_features.update(current_config)
            except Exception as stats_error:
                print(f"Error getting stats: {stats_error}")
                stats = {'database_file_size_mb': 0, 'total_records': 0}
                security_features = {'encryption_enabled': True, 'compression_enabled': True, 'compression_type': 'gzip', 'checksums_enabled': True}
                table_stats = {}
            
            def close_dialog(dialog_ref):
                dialog_ref.open = False
                page.update()
            
            def refresh_dialog(e):
                close_dialog(settings_dialog)
                show_settings_dialog(e)
            
            def toggle_encryption(e):
                try:
                    new_state = not security_features.get('encryption_enabled', True)
                    success = secure_db.update_security_settings(encryption=new_state)
                    if success:
                        show_snackbar(f"✓ Encryption {'enabled' if new_state else 'disabled'} successfully!")
                        # Auto-save current app data with new settings
                        secure_db.save_app_data(app_data)
                        # Refresh dialog to show new state
                        refresh_dialog(e)
                    else:
                        show_snackbar("❌ Failed to update encryption setting")
                except Exception as err:
                    show_snackbar(f"❌ Error toggling encryption: {str(err)}")
            
            def toggle_compression(e):
                try:
                    new_state = not security_features.get('compression_enabled', True)
                    success = secure_db.update_security_settings(compression=new_state)
                    if success:
                        show_snackbar(f"✓ Compression {'enabled' if new_state else 'disabled'} successfully!")
                        # Auto-save current app data with new settings
                        secure_db.save_app_data(app_data)
                        # Refresh dialog to show new state
                        refresh_dialog(e)
                    else:
                        show_snackbar("❌ Failed to update compression setting")
                except Exception as err:
                    show_snackbar(f"❌ Error toggling compression: {str(err)}")
            
            def toggle_checksums(e):
                try:
                    new_state = not security_features.get('checksums_enabled', True)
                    success = secure_db.update_security_settings(checksums=new_state)
                    if success:
                        show_snackbar(f"✓ Data integrity {'enabled' if new_state else 'disabled'} successfully!")
                        # Auto-save current app data with new settings
                        secure_db.save_app_data(app_data)
                        # Refresh dialog to show new state
                        refresh_dialog(e)
                    else:
                        show_snackbar("❌ Failed to update checksums setting")
                except Exception as err:
                    show_snackbar(f"❌ Error toggling checksums: {str(err)}")
            
            # Create simpler settings content
            settings_content = ft.Column([
                # Title
                ft.Text("Settings & Information", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                # Security Configuration Section
                ft.Text("Security Configuration", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                ft.Container(height=5),
                
                # Encryption Toggle
                ft.Row([
                    ft.Switch(
                        value=security_features.get('encryption_enabled', True),
                        on_change=toggle_encryption,
                        active_color=ft.colors.GREEN_600
                    ),
                    ft.Text(f"AES-256 Encryption: {'Enabled' if security_features.get('encryption_enabled') else 'Disabled'}", 
                           color=ft.colors.GREEN_600 if security_features.get('encryption_enabled') else ft.colors.ORANGE_600)
                ], spacing=10),
                
                # Compression Toggle
                ft.Row([
                    ft.Switch(
                        value=security_features.get('compression_enabled', True),
                        on_change=toggle_compression,
                        active_color=ft.colors.GREEN_600
                    ),
                    ft.Text(f"{security_features.get('compression_type', 'GZIP').upper()} Compression: "
                           f"{'Enabled' if security_features.get('compression_enabled') else 'Disabled'}",
                           color=ft.colors.GREEN_600 if security_features.get('compression_enabled') else ft.colors.ORANGE_600)
                ], spacing=10),
                
                # Data Integrity Toggle
                ft.Row([
                    ft.Switch(
                        value=security_features.get('checksums_enabled', True),
                        on_change=toggle_checksums,
                        active_color=ft.colors.GREEN_600
                    ),
                    ft.Text(f"Data Integrity (SHA-256): {'Enabled' if security_features.get('checksums_enabled') else 'Disabled'}",
                           color=ft.colors.GREEN_600 if security_features.get('checksums_enabled') else ft.colors.ORANGE_600)
                ], spacing=10),
                
                ft.Container(height=15),
                
                # Storage Section
                ft.Text("Storage Information", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE_700),
                ft.Container(height=5),
                
                ft.Text(f"Database Size: {stats.get('database_file_size_mb', 0):.2f} MB"),
                ft.Text(f"Total Records: {stats.get('total_records', 0)}"),
                
                ft.Container(height=10),
                
                # Table stats (if available)
                ft.Text("Table Statistics:", size=14, weight=ft.FontWeight.W_500) if table_stats else ft.Container(),
            ] + [
                ft.Text(f"  • {table}: {info.get('records', 0)} records", size=12, color=ft.colors.GREY_600) 
                for table, info in table_stats.items()
            ] + [
                ft.Container(height=15),
                
                # Actions
                ft.Text("Actions", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE_700),
                ft.Container(height=10),
                
                ft.Row([
                    ft.ElevatedButton(
                        "Backup Data",
                        icon=ft.icons.BACKUP,
                        on_click=backup_data,
                        bgcolor=ft.colors.GREEN_600,
                        color=ft.colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "Import Backup",
                        icon=ft.icons.UPLOAD,
                        on_click=restore_database_from_backup,
                        bgcolor=ft.colors.BLUE_600,
                        color=ft.colors.WHITE
                    )
                ], spacing=10),
                
                # Admin-only operations section
                ft.Container(height=15),
                ft.Row([
                    ft.ElevatedButton(
                        "Export CSV",
                        icon=ft.icons.TABLE_CHART,
                        on_click=lambda e: show_export_dialog(),
                        bgcolor=ft.colors.PURPLE_600,
                        color=ft.colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "Refresh",
                        icon=ft.icons.REFRESH,
                        on_click=refresh_dialog,
                        bgcolor=ft.colors.GREY_600,
                        color=ft.colors.WHITE
                    )
                ], spacing=10),
                
                # Admin-only dangerous operations
                ft.Container(height=15),
                ft.Text("Dangerous Operations (Admin Only)", size=14, weight=ft.FontWeight.BOLD, 
                       color=ft.colors.RED_700) if check_permission('all') else ft.Container(),
                ft.Text("⚠️ These operations require admin privileges and may permanently affect data", 
                       size=12, color=ft.colors.ORANGE_600) if check_permission('all') else ft.Container(),
                ft.Container(height=5) if check_permission('all') else ft.Container(),
                
                ft.Row([
                    ft.ElevatedButton(
                        "Empty Database",
                        icon=ft.icons.DELETE_FOREVER,
                        on_click=clear_database,
                        bgcolor=ft.colors.RED_600,
                        color=ft.colors.WHITE
                    )
                ], spacing=10) if check_permission('all') else ft.Container(),
                
                ft.Container(height=15),
                
                # Info
                ft.Container(
                    content=ft.Column([
                        ft.Text("Security Information:", weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "• Encryption: AES-256 protects sensitive data\n"
                            "• Compression: GZIP reduces storage by 60-80%\n"
                            "• Data Integrity: SHA-256 detects corruption\n"
                            "• Settings: Changes apply immediately\n"
                            "• Backward Compatible: Handles mixed states",
                            size=12,
                            color=ft.colors.GREY_700
                        )
                    ], spacing=5),
                    padding=15,
                    bgcolor=ft.colors.BLUE_50,
                    border_radius=8
                )
            ], scroll=ft.ScrollMode.AUTO, spacing=8)
            
            # Create the dialog
            settings_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Settings"),
                content=ft.Container(
                    content=settings_content,
                    width=450,
                    height=500
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: close_dialog(settings_dialog))
                ]
            )
            
            page.dialog = settings_dialog
            settings_dialog.open = True
            page.update()
            
        except Exception as e:
            print(f"Error in show_settings_dialog: {e}")
            # Create simple fallback dialog
            try:
                def close_simple_dialog(dialog_ref):
                    dialog_ref.open = False
                    page.update()
                
                simple_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Settings"),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Application Settings", size=18, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            ft.Text("Security Status:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text("✓ Encryption: AES-256 Enabled", color=ft.colors.GREEN_600),
                            ft.Text("✓ Compression: GZIP Enabled", color=ft.colors.GREEN_600),
                            ft.Text("✓ Data Integrity: SHA-256 Enabled", color=ft.colors.GREEN_600),
                            ft.Container(height=15),
                            ft.Text("Features:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text("• All data is automatically encrypted", size=12),
                            ft.Text("• Compression reduces storage size", size=12),
                            ft.Text("• Data integrity is verified", size=12),
                            ft.Text("• Backups are encrypted", size=12),
                            ft.Container(height=15),
                            ft.ElevatedButton(
                                "Create Backup",
                                icon=ft.icons.BACKUP,
                                on_click=backup_data,
                                bgcolor=ft.colors.GREEN_600,
                                color=ft.colors.WHITE
                            )
                        ], spacing=8),
                        width=350,
                        height=400
                    ),
                    actions=[
                        ft.TextButton("Close", on_click=lambda e: close_simple_dialog(simple_dialog))
                    ]
                )
                
                page.dialog = simple_dialog
                simple_dialog.open = True
                page.update()
                
            except Exception as fallback_error:
                print(f"Fallback dialog also failed: {fallback_error}")
                show_snackbar(f"Settings: Encryption ✓, Compression ✓, Data Integrity ✓")
    
    # CRUD Operations for Handovers
    def show_handover_form(handover_data=None):
        """Show handover form dialog."""
        is_edit = handover_data is not None
        
        # Form fields
        from_team_field = ft.TextField(
            label="From Team",
            value=handover_data.get("from_team", "") if is_edit else "",
            width=350
        )
        to_team_field = ft.TextField(
            label="To Team",
            value=handover_data.get("to_team", "") if is_edit else "",
            width=350
        )
        description_field = ft.TextField(
            label="Description",
            value=handover_data.get("description", "") if is_edit else "",
            multiline=True,
            width=350,
            max_lines=3
        )
        date_field = ft.TextField(
            label="Date (YYYY-MM-DD)",
            value=handover_data.get("date", "2024-01-16") if is_edit else "2024-01-16",
            width=350
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            value=handover_data.get("status", "Pending") if is_edit else "Pending",
            options=[
                ft.dropdown.Option("Pending"),
                ft.dropdown.Option("In Progress"),
                ft.dropdown.Option("Completed")
            ],
            width=350
        )
        
        def save_handover(e):
            # Validate fields
            if not from_team_field.value or not to_team_field.value:
                show_snackbar("Please fill in both From Team and To Team fields!")
                return
                
            if is_edit:
                # Update existing handover
                handover_data["from_team"] = from_team_field.value
                handover_data["to_team"] = to_team_field.value
                handover_data["description"] = description_field.value
                handover_data["date"] = date_field.value
                handover_data["status"] = status_dropdown.value
                add_activity("Handover", f"Updated handover: {handover_data['from_team']} → {handover_data['to_team']}", handover_data['id'])
                show_snackbar(f"Handover #{handover_data['id']} updated successfully!")
            else:
                # Add new handover
                new_id = max([h["id"] for h in app_data["handovers"]], default=0) + 1
                new_handover = {
                    "id": new_id,
                    "from_team": from_team_field.value,
                    "to_team": to_team_field.value,
                    "description": description_field.value,
                    "date": date_field.value,
                    "status": status_dropdown.value
                }
                app_data["handovers"].append(new_handover)
                add_activity("Handover", f"Created handover: {from_team_field.value} → {to_team_field.value}", new_id)
                show_snackbar(f"Handover #{new_id} added successfully!")
            
            close_dialog(dialog)
            # Auto-save data after any changes
            secure_db.save_app_data(app_data)
            refresh_current_tab()
        
        def close_dialog(dialog_ref):
            dialog_ref.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Handover" if is_edit else "New Handover"),
            content=ft.Container(
                content=ft.Column([
                    from_team_field,
                    to_team_field,
                    description_field,
                    date_field,
                    status_dropdown
                ], spacing=10),
                width=400,
                height=350
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(dialog)),
                ft.ElevatedButton(
                    "Save", 
                    on_click=save_handover,
                    bgcolor=ft.colors.BLUE_600,
                    color=ft.colors.WHITE
                )
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def add_handover(e):
        """Show form to add new handover."""
        if not require_permission('write'):
            return
        show_handover_form()
    
    def edit_handover(handover_id):
        """Show form to edit handover."""
        if not require_permission('write'):
            return
        try:
            handover = next(h for h in app_data["handovers"] if h["id"] == handover_id)
            show_handover_form(handover)
        except StopIteration:
            show_snackbar(f"Handover #{handover_id} not found!")
    
    def delete_handover(handover_id):
        """Delete handover."""
        if not require_permission('write'):
            return
        # Get handover info before deleting for activity log
        handover = next((h for h in app_data["handovers"] if h["id"] == handover_id), None)
        if handover:
            add_activity("Handover", f"Deleted handover: {handover.get('from_team', 'Unknown')} → {handover.get('to_team', 'Unknown')}", handover_id)
        
        app_data["handovers"] = [h for h in app_data["handovers"] if h["id"] != handover_id]
        # Auto-save after deletion
        secure_db.save_app_data(app_data)
        show_snackbar(f"Handover #{handover_id} deleted successfully!")
        refresh_current_tab()
    
    # CRUD Operations for Requirements
    def show_requirement_form(req_data=None):
        """Show requirement form dialog."""
        is_edit = req_data is not None
        
        title_field = ft.TextField(
            label="Title",
            value=req_data.get("title", "") if is_edit else "",
            width=350,
            hint_text="REQ-001: Requirement title"
        )
        description_field = ft.TextField(
            label="Description",
            value=req_data.get("description", "") if is_edit else "",
            multiline=True,
            width=350,
            max_lines=4
        )
        priority_dropdown = ft.Dropdown(
            label="Priority",
            value=req_data.get("priority", "Medium") if is_edit else "Medium",
            options=[
                ft.dropdown.Option("Low"),
                ft.dropdown.Option("Medium"), 
                ft.dropdown.Option("High"),
                ft.dropdown.Option("Critical")
            ],
            width=350
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            value=req_data.get("status", "New") if is_edit else "New",
            options=[
                ft.dropdown.Option("New"),
                ft.dropdown.Option("In Development"),
                ft.dropdown.Option("Completed"),
                ft.dropdown.Option("On Hold")
            ],
            width=350
        )
        
        def save_requirement(e):
            if not title_field.value or not description_field.value:
                show_snackbar("Please fill in both Title and Description fields!")
                return
            
            if is_edit:
                req_data["title"] = title_field.value
                req_data["description"] = description_field.value
                req_data["priority"] = priority_dropdown.value
                req_data["status"] = status_dropdown.value
                add_activity("Requirement", f"Updated requirement: {title_field.value}", req_data['id'])
                show_snackbar(f"Requirement #{req_data['id']} updated successfully!")
            else:
                new_id = max([r["id"] for r in app_data["requirements"]], default=0) + 1
                new_req = {
                    "id": new_id,
                    "title": title_field.value,
                    "description": description_field.value,
                    "priority": priority_dropdown.value,
                    "status": status_dropdown.value
                }
                app_data["requirements"].append(new_req)
                add_activity("Requirement", f"Created requirement: {title_field.value}", new_id)
                show_snackbar(f"Requirement #{new_id} added successfully!")
            
            close_dialog(dialog)
            refresh_current_tab()
        
        def close_dialog(dialog_ref):
            dialog_ref.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Requirement" if is_edit else "New Requirement"),
            content=ft.Container(
                content=ft.Column([
                    title_field,
                    description_field,
                    priority_dropdown,
                    status_dropdown
                ], spacing=10),
                width=400,
                height=300
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(dialog)),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_requirement,
                    bgcolor=ft.colors.GREEN_600,
                    color=ft.colors.WHITE
                )
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def add_requirement(e):
        """Show form to add new requirement."""
        show_requirement_form()
    
    def edit_requirement(req_id):
        """Show form to edit requirement."""
        try:
            req = next(r for r in app_data["requirements"] if r["id"] == req_id)
            show_requirement_form(req)
        except StopIteration:
            show_snackbar(f"Requirement #{req_id} not found!")
    
    def delete_requirement(req_id):
        """Delete requirement."""
        # Get requirement info before deleting for activity log
        req = next((r for r in app_data["requirements"] if r["id"] == req_id), None)
        if req:
            add_activity("Requirement", f"Deleted requirement: {req['title']}", req_id)
        
        app_data["requirements"] = [r for r in app_data["requirements"] if r["id"] != req_id]
        show_snackbar(f"Requirement #{req_id} deleted successfully!")
        refresh_current_tab()
    
    # CRUD Operations for Issues
    def show_issue_form(issue_data=None):
        """Show issue form dialog."""
        is_edit = issue_data is not None
        
        title_field = ft.TextField(
            label="Title",
            value=issue_data.get("title", "") if is_edit else "",
            width=350,
            hint_text="ISS-001: Issue title"
        )
        description_field = ft.TextField(
            label="Description",
            value=issue_data.get("description", "") if is_edit else "",
            multiline=True,
            width=350,
            max_lines=4
        )
        priority_dropdown = ft.Dropdown(
            label="Priority",
            value=issue_data.get("priority", "Medium") if is_edit else "Medium",
            options=[
                ft.dropdown.Option("Low"),
                ft.dropdown.Option("Medium"),
                ft.dropdown.Option("High"),
                ft.dropdown.Option("Critical")
            ],
            width=350
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            value=issue_data.get("status", "Open") if is_edit else "Open",
            options=[
                ft.dropdown.Option("Open"),
                ft.dropdown.Option("In Progress"),
                ft.dropdown.Option("Testing"),
                ft.dropdown.Option("Resolved"),
                ft.dropdown.Option("Closed")
            ],
            width=350
        )
        # Get list of users for assignment dropdown
        user_name_to_username = {"Unassigned": None}  # Mapping from display name to username
        
        try:
            users_list = auth_service.get_all_users()
            print(f"Debug: Found {len(users_list) if users_list else 0} users")
            user_options = [ft.dropdown.Option("Unassigned")]
            
            if users_list:
                for user in users_list:
                    full_name = user.get_full_name()
                    username = user.username
                    print(f"Debug: Adding user {full_name} ({username})")
                    user_options.append(ft.dropdown.Option(full_name))
                    user_name_to_username[full_name] = username
            else:
                print("Debug: No users found in database")
                
        except Exception as e:
            print(f"Error getting users for assignment: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: create some default users if auth service fails
            print("Debug: Using fallback user list")
            user_options = [
                ft.dropdown.Option("Unassigned"),
                ft.dropdown.Option("Admin User"),
                ft.dropdown.Option("John Doe"),
                ft.dropdown.Option("Jane Smith"),
                ft.dropdown.Option("Backend Team"),
                ft.dropdown.Option("Frontend Team"),
                ft.dropdown.Option("QA Team")
            ]
            user_name_to_username = {
                "Unassigned": None,
                "Admin User": "admin",
                "John Doe": "john.doe",
                "Jane Smith": "jane.smith",
                "Backend Team": "backend",
                "Frontend Team": "frontend",
                "QA Team": "qa"
            }
        
        # Find current assigned user for editing
        current_assigned = "Unassigned"
        if is_edit and issue_data.get("assigned"):
            assigned_username = issue_data.get("assigned_username", "")
            if assigned_username and users_list:
                try:
                    assigned_user = next(u for u in users_list if u.username == assigned_username)
                    current_assigned = assigned_user.get_full_name()
                    print(f"Debug: Found assigned user: {current_assigned}")
                except:
                    current_assigned = issue_data.get("assigned", "Unassigned")
                    print(f"Debug: Could not find user with username {assigned_username}, using fallback: {current_assigned}")
            else:
                current_assigned = issue_data.get("assigned", "Unassigned")
                print(f"Debug: No assigned username, using: {current_assigned}")
        
        print(f"Debug: Creating dropdown with {len(user_options)} options, current value: {current_assigned}")
        assigned_dropdown = ft.Dropdown(
            label="Assigned To",
            value=current_assigned,
            options=user_options,
            width=350
        )
        
        def save_issue(e):
            if not title_field.value or not description_field.value:
                show_snackbar("Please fill in both Title and Description fields!")
                return
            
            # Get assigned user info
            assigned_user_name = assigned_dropdown.value
            assigned_username = user_name_to_username.get(assigned_user_name)
            
            print(f"Debug: Selected user: {assigned_user_name}, username: {assigned_username}")
            
            from datetime import datetime
            
            if is_edit:
                old_assigned = issue_data.get("assigned_username")
                issue_data["title"] = title_field.value
                issue_data["description"] = description_field.value
                issue_data["priority"] = priority_dropdown.value
                issue_data["status"] = status_dropdown.value
                issue_data["assigned"] = assigned_user_name or "Unassigned"
                issue_data["assigned_username"] = assigned_username
                
                # Send notification if assignment changed
                if assigned_username and old_assigned != assigned_username:
                    try:
                        auth_service.create_user_notification(
                            username=assigned_username,
                            subject=f"Issue Assigned: {title_field.value}",
                            message=f"You have been assigned to issue #{issue_data['id']}: {title_field.value}\n\nPriority: {priority_dropdown.value}\nDescription: {description_field.value}",
                            notification_type="info"
                        )
                    except Exception as e:
                        print(f"Error sending assignment notification: {e}")
                
                add_activity("Issue", f"Updated issue: {title_field.value}", issue_data['id'])
                show_snackbar(f"Issue #{issue_data['id']} updated successfully!")
            else:
                new_id = max([i["id"] for i in app_data["issues"]], default=0) + 1
                new_issue = {
                    "id": new_id,
                    "title": title_field.value,
                    "description": description_field.value,
                    "type": "infra",  # Default type, can be changed later
                    "priority": priority_dropdown.value,
                    "status": status_dropdown.value,
                    "assigned": assigned_user_name or "Unassigned",
                    "assigned_username": assigned_username,
                    "created_by": current_user.get_full_name() if current_user else "Unknown",
                    "created_by_username": current_user.username if current_user else "unknown",
                    "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                app_data["issues"].append(new_issue)
                
                # Send notification to assigned user
                if assigned_username:
                    try:
                        auth_service.create_user_notification(
                            username=assigned_username,
                            subject=f"New Issue Assigned: {title_field.value}",
                            message=f"A new issue has been assigned to you by {current_user.get_full_name() if current_user else 'Unknown'}:\n\nIssue #{new_id}: {title_field.value}\nPriority: {priority_dropdown.value}\nDescription: {description_field.value}",
                            notification_type="info"
                        )
                    except Exception as e:
                        print(f"Error sending assignment notification: {e}")
                
                add_activity("Issue", f"Reported issue: {title_field.value}", new_id)
                show_snackbar(f"Issue #{new_id} reported successfully!")
            
            close_dialog(dialog)
            secure_db.save_app_data(app_data)
            refresh_current_tab()
        
        def close_dialog(dialog_ref):
            dialog_ref.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Issue" if is_edit else "Report New Issue"),
            content=ft.Container(
                content=ft.Column([
                    title_field,
                    description_field,
                    priority_dropdown,
                    status_dropdown,
                    assigned_dropdown
                ], spacing=10),
                width=400,
                height=350
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(dialog)),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_issue,
                    bgcolor=ft.colors.RED_600,
                    color=ft.colors.WHITE
                )
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def add_issue(e):
        """Show form to add new issue."""
        show_issue_form()
    
    def edit_issue(issue_id):
        """Show form to edit issue."""
        try:
            issue = next(i for i in app_data["issues"] if i["id"] == issue_id)
            show_issue_form(issue)
        except StopIteration:
            show_snackbar(f"Issue #{issue_id} not found!")
    
    def delete_issue(issue_id):
        """Delete issue."""
        # Get issue info before deleting for activity log
        issue = next((i for i in app_data["issues"] if i["id"] == issue_id), None)
        if issue:
            add_activity("Issue", f"Deleted issue: {issue['title']}", issue_id)
        
        app_data["issues"] = [i for i in app_data["issues"] if i["id"] != issue_id]
        show_snackbar(f"Issue #{issue_id} deleted successfully!")
        refresh_current_tab()
    
    # CRUD Operations for Test Suites
    def show_test_suite_form(suite_data=None):
        """Show test suite form dialog."""
        is_edit = suite_data is not None
        
        name_field = ft.TextField(
            label="Test Suite Name",
            value=suite_data.get("name", "") if is_edit else "",
            width=350,
            hint_text="Authentication Tests, API Tests, etc."
        )
        total_tests_field = ft.TextField(
            label="Total Tests",
            value=str(suite_data.get("total", 5)) if is_edit else "5",
            width=350,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="Number of tests in this suite"
        )
        type_dropdown = ft.Dropdown(
            label="Test Suite Type",
            value=suite_data.get("type", "Smoke") if is_edit else "Smoke",
            options=[
                ft.dropdown.Option("Smoke"),
                ft.dropdown.Option("Full")
            ],
            width=350
        )
        
        status_dropdown = ft.Dropdown(
            label="Status",
            value=suite_data.get("status", "Not Run") if is_edit else "Not Run",
            options=[
                ft.dropdown.Option("Not Run"),
                ft.dropdown.Option("Running"),
                ft.dropdown.Option("Passed"),
                ft.dropdown.Option("Failed")
            ],
            width=350
        )
        
        # Only show passed tests field if editing and status allows it
        passed_tests_field = None
        if is_edit and suite_data.get("status") in ["Passed", "Failed"]:
            passed_tests_field = ft.TextField(
                label="Tests Passed",
                value=str(suite_data.get("passed", 0)),
                width=350,
                keyboard_type=ft.KeyboardType.NUMBER
            )
        
        def save_test_suite(e):
            if not name_field.value:
                show_snackbar("Please fill in the Test Suite Name!")
                return
            
            try:
                total_tests = int(total_tests_field.value) if total_tests_field.value else 1
                if total_tests < 1:
                    show_snackbar("Total tests must be at least 1!")
                    return
            except ValueError:
                show_snackbar("Please enter a valid number for total tests!")
                return
            
            if is_edit:
                suite_data["name"] = name_field.value
                suite_data["type"] = type_dropdown.value
                suite_data["total"] = total_tests
                suite_data["status"] = status_dropdown.value
                if passed_tests_field:
                    try:
                        passed = int(passed_tests_field.value) if passed_tests_field.value else 0
                        suite_data["passed"] = min(passed, total_tests)  # Can't pass more than total
                    except ValueError:
                        pass  # Keep existing value if invalid
                add_activity("Test Suite", f"Updated test suite: {name_field.value}", suite_data['id'])
                show_snackbar(f"Test Suite #{suite_data['id']} updated successfully!")
            else:
                new_id = max([ts["id"] for ts in app_data["test_suites"]], default=0) + 1
                new_suite = {
                    "id": new_id,
                    "name": name_field.value,
                    "type": type_dropdown.value,
                    "status": status_dropdown.value,
                    "last_run": "Never" if status_dropdown.value == "Not Run" else "2024-01-16 15:30",
                    "passed": 0,
                    "total": total_tests,
                    "duration": "0.0s"
                }
                app_data["test_suites"].append(new_suite)
                add_activity("Test Suite", f"Created test suite: {name_field.value}", new_id)
                show_snackbar(f"Test Suite #{new_id} added successfully!")
            
            close_dialog(dialog)
            refresh_current_tab()
        
        def close_dialog(dialog_ref):
            dialog_ref.open = False
            page.update()
        
        # Build form fields list
        form_fields = [name_field, type_dropdown, total_tests_field, status_dropdown]
        if passed_tests_field:
            form_fields.append(passed_tests_field)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Test Suite" if is_edit else "New Test Suite"),
            content=ft.Container(
                content=ft.Column(form_fields, spacing=10),
                width=400,
                height=250 if not passed_tests_field else 300
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(dialog)),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_test_suite,
                    bgcolor=ft.colors.ORANGE_600,
                    color=ft.colors.WHITE
                )
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def add_test_suite(e):
        """Show form to add new test suite."""
        show_test_suite_form()
    
    def run_test_suite(suite_id):
        """Run test suite (simulate)."""
        suite = next(ts for ts in app_data["test_suites"] if ts["id"] == suite_id)
        import random
        suite["passed"] = random.randint(suite["total"]-2, suite["total"])
        suite["status"] = "Passed" if suite["passed"] == suite["total"] else "Failed"
        suite["last_run"] = "2024-01-16 15:30"
        suite["duration"] = f"{random.uniform(1.0, 10.0):.1f}s"
        add_activity("Test Suite", f"Executed test suite: {suite['name']} ({suite['passed']}/{suite['total']} passed)", suite_id)
        show_snackbar(f"Test Suite #{suite_id} executed: {suite['passed']}/{suite['total']} passed")
        refresh_current_tab()
    
    def edit_test_suite(suite_id):
        """Show form to edit test suite."""
        try:
            suite = next(ts for ts in app_data["test_suites"] if ts["id"] == suite_id)
            show_test_suite_form(suite)
        except StopIteration:
            show_snackbar(f"Test Suite #{suite_id} not found!")
    
    def delete_test_suite(suite_id):
        """Delete test suite."""
        # Get test suite info before deleting for activity log
        suite = next((ts for ts in app_data["test_suites"] if ts["id"] == suite_id), None)
        if suite:
            add_activity("Test Suite", f"Deleted test suite: {suite['name']}", suite_id)
        
        app_data["test_suites"] = [ts for ts in app_data["test_suites"] if ts["id"] != suite_id]
        show_snackbar(f"Test Suite #{suite_id} deleted successfully!")
        refresh_current_tab()
    
    # Bench CRUD Functions
    def add_bench(e):
        """Show form to add new bench."""
        if not require_permission('write'):
            return
        show_bench_form()
    
    def show_bench_form(bench_data=None):
        """Show bench form dialog."""
        is_edit = bench_data is not None
        
        name_field = ft.TextField(
            label="Bench Name",
            value=bench_data.get("name", "") if is_edit else "",
            width=350,
            hint_text="Development Bench 1"
        )
        
        status_dropdown = ft.Dropdown(
            label="Status",
            value=bench_data.get("status", "Available") if is_edit else "Available",
            options=[
                ft.dropdown.Option("Available"),
                ft.dropdown.Option("Occupied"),
                ft.dropdown.Option("Maintenance"),
                ft.dropdown.Option("Reserved")
            ],
            width=350
        )
        
        assigned_field = ft.TextField(
            label="Assigned To",
            value=bench_data.get("assigned_to", "") if is_edit else "",
            width=350,
            hint_text="Team or Person Name"
        )
        
        project_field = ft.TextField(
            label="Project",
            value=bench_data.get("project", "") if is_edit else "",
            width=350,
            hint_text="Project Name"
        )
        
        def save_bench(e):
            if not name_field.value:
                show_snackbar("Please fill in the bench name!")
                return
            
            from datetime import datetime
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            if is_edit:
                bench_data["name"] = name_field.value
                bench_data["status"] = status_dropdown.value
                bench_data["assigned_to"] = assigned_field.value or ""
                bench_data["project"] = project_field.value or ""
                bench_data["last_updated"] = current_date
                add_activity("Bench", f"Updated bench: {bench_data['name']}", bench_data['id'])
                show_snackbar(f"Bench #{bench_data['id']} updated successfully!")
            else:
                new_id = max([b["id"] for b in app_data.get("benches", [])], default=0) + 1
                new_bench = {
                    "id": new_id,
                    "name": name_field.value,
                    "status": status_dropdown.value,
                    "assigned_to": assigned_field.value or "",
                    "project": project_field.value or "",
                    "last_updated": current_date
                }
                if "benches" not in app_data:
                    app_data["benches"] = []
                app_data["benches"].append(new_bench)
                add_activity("Bench", f"Created bench: {name_field.value}", new_id)
                show_snackbar(f"Bench #{new_id} added successfully!")
            
            close_dialog(dialog)
            secure_db.save_app_data(app_data)
            refresh_current_tab()
        
        def close_dialog(dialog_ref):
            dialog_ref.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Bench" if is_edit else "New Bench"),
            content=ft.Container(
                content=ft.Column([
                    name_field,
                    status_dropdown,
                    assigned_field,
                    project_field
                ], spacing=10),
                width=400,
                height=300
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(dialog)),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_bench,
                    bgcolor=ft.colors.BLUE_600,
                    color=ft.colors.WHITE
                )
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    # Knowledge Article CRUD Functions
    def add_article(e):
        """Show form to add new knowledge article."""
        if not require_permission('write'):
            return
        show_article_form()
    
    def show_article_form(article_data=None):
        """Show article form dialog."""
        is_edit = article_data is not None
        
        title_field = ft.TextField(
            label="Title",
            value=article_data.get("title", "") if is_edit else "",
            width=500,
            hint_text="How to Setup Development Environment"
        )
        
        content_field = ft.TextField(
            label="Content",
            value=article_data.get("content", "") if is_edit else "",
            multiline=True,
            width=500,
            max_lines=8,
            hint_text="Enter the knowledge article content..."
        )
        
        tags_field = ft.TextField(
            label="Tags (comma separated)",
            value=", ".join(article_data.get("tags", [])) if is_edit else "",
            width=500,
            hint_text="setup, development, guide"
        )
        
        def save_article(e):
            if not title_field.value or not content_field.value:
                show_snackbar("Please fill in title and content!")
                return
            
            from datetime import datetime
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Process tags
            tags = [tag.strip() for tag in tags_field.value.split(",")] if tags_field.value else []
            
            if is_edit:
                article_data["title"] = title_field.value
                article_data["content"] = content_field.value
                article_data["tags"] = tags
                add_activity("Knowledge", f"Updated article: {article_data['title']}", article_data['id'])
                show_snackbar(f"Article #{article_data['id']} updated successfully!")
            else:
                new_id = max([a["id"] for a in app_data.get("knowledge_articles", [])], default=0) + 1
                new_article = {
                    "id": new_id,
                    "title": title_field.value,
                    "content": content_field.value,
                    "author": current_user.get_full_name() if current_user else "Unknown",
                    "created_date": current_date,
                    "tags": tags,
                    "comments": []
                }
                if "knowledge_articles" not in app_data:
                    app_data["knowledge_articles"] = []
                app_data["knowledge_articles"].append(new_article)
                add_activity("Knowledge", f"Created article: {title_field.value}", new_id)
                show_snackbar(f"Article #{new_id} added successfully!")
            
            close_dialog(dialog)
            secure_db.save_app_data(app_data)
            refresh_current_tab()
        
        def close_dialog(dialog_ref):
            dialog_ref.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Article" if is_edit else "New Knowledge Article"),
            content=ft.Container(
                content=ft.Column([
                    title_field,
                    content_field,
                    tags_field
                ], spacing=10),
                width=550,
                height=400
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(dialog)),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_article,
                    bgcolor=ft.colors.BLUE_600,
                    color=ft.colors.WHITE
                )
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def view_article(article_id):
        """Show article with comments."""
        try:
            article = next(a for a in app_data.get("knowledge_articles", []) if a["id"] == article_id)
            show_article_view_dialog(article)
        except StopIteration:
            show_snackbar(f"Article #{article_id} not found!")
    
    def show_article_view_dialog(article):
        """Show article view with comments."""
        def close_dialog(dialog_ref):
            dialog_ref.open = False
            page.update()
        
        def add_comment(e):
            if not comment_field.value:
                show_snackbar("Please enter a comment!")
                return
            
            from datetime import datetime
            new_comment = {
                "id": max([c.get("id", 0) for c in article.get("comments", [])], default=0) + 1,
                "author": current_user.get_full_name() if current_user else "Anonymous",
                "content": comment_field.value,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if "comments" not in article:
                article["comments"] = []
            article["comments"].append(new_comment)
            
            secure_db.save_app_data(app_data)
            comment_field.value = ""
            close_dialog(view_dialog)
            # Reopen with updated comments
            show_article_view_dialog(article)
        
        # Create comments display
        comment_items = []
        for comment in article.get("comments", []):
            comment_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(comment.get("author", "Unknown"), weight=ft.FontWeight.BOLD, size=14),
                            ft.Text(comment.get("date", ""), size=12, color=ft.colors.GREY_600)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(comment.get("content", ""), size=14)
                    ]),
                    padding=10,
                    bgcolor=ft.colors.GREY_100,
                    border_radius=5
                )
            )
        
        # Comment input field
        comment_field = ft.TextField(
            label="Add a comment",
            multiline=True,
            max_lines=3,
            width=500
        )
        
        view_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(article.get("title", "Article")),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"By: {article.get('author', 'Unknown')} | {article.get('created_date', '')}", 
                           size=12, color=ft.colors.GREY_600),
                    ft.Container(height=10),
                    ft.Text(article.get("content", "No content"), size=14),
                    ft.Container(height=20),
                    ft.Text("Comments", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Column(comment_items, spacing=10) if comment_items else ft.Text("No comments yet", color=ft.colors.GREY_600),
                    ft.Container(height=15),
                    comment_field,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Add Comment",
                        icon=ft.icons.ADD,
                        on_click=add_comment,
                        bgcolor=ft.colors.BLUE_600,
                        color=ft.colors.WHITE
                    )
                ], spacing=5, scroll=ft.ScrollMode.AUTO),
                width=550,
                height=500
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: close_dialog(view_dialog))
            ]
        )
        
        page.dialog = view_dialog
        view_dialog.open = True
        page.update()
    
    def edit_article(article_id):
        """Show form to edit article."""
        if not require_permission('write'):
            return
        try:
            article = next(a for a in app_data.get("knowledge_articles", []) if a["id"] == article_id)
            show_article_form(article)
        except StopIteration:
            show_snackbar(f"Article #{article_id} not found!")
    
    def delete_article(article_id):
        """Delete article."""
        if not require_permission('write'):
            return
        article = next((a for a in app_data.get("knowledge_articles", []) if a["id"] == article_id), None)
        if article:
            add_activity("Knowledge", f"Deleted article: {article['title']}", article_id)
        
        if "knowledge_articles" in app_data:
            app_data["knowledge_articles"] = [a for a in app_data["knowledge_articles"] if a["id"] != article_id]
        secure_db.save_app_data(app_data)
        show_snackbar(f"Article #{article_id} deleted successfully!")
        refresh_current_tab()
    
    def create_proposals_content():
        """Create anonymous proposals tab content with dynamic data."""
        proposal_cards = []
        
        for proposal in sorted(app_data.get("anonymous_proposals", []), key=lambda x: x["id"], reverse=True):
            status_colors = {
                "Pending Review": ft.colors.ORANGE_100,
                "Under Review": ft.colors.BLUE_100,
                "Approved": ft.colors.GREEN_100,
                "Rejected": ft.colors.RED_100,
                "Implemented": ft.colors.PURPLE_100
            }
            
            # Show admin response if available
            response_section = []
            if proposal.get("admin_response") and check_permission('all'):
                response_section = [
                    ft.Container(height=10),
                    ft.Text("Admin Response:", weight=ft.FontWeight.BOLD, size=12, color=ft.colors.GREY_700),
                    ft.Text(proposal.get("admin_response", ""), size=12, color=ft.colors.GREY_600),
                    ft.Text(f"Response Date: {proposal.get('response_date', '')}", size=10, color=ft.colors.GREY_500)
                ]
            
            proposal_cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(proposal.get("title", "Untitled Proposal"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Chip(label=ft.Text(proposal.get("status", "Pending Review")), bgcolor=status_colors.get(proposal.get("status", "Pending Review"), ft.colors.GREY_100))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(proposal.get("description", "No description")[:200] + "..." if len(proposal.get("description", "")) > 200 else proposal.get("description", "No description"), size=14),
                            ft.Container(height=5),
                            ft.Text(f"Submitted: {proposal.get('submitted_date', 'Unknown')}", size=12, color=ft.colors.GREY_600),
                            *response_section,
                            ft.Container(height=10),
                            ft.Row([
                                ft.ElevatedButton(
                                    "View Details",
                                    icon=ft.icons.VISIBILITY,
                                    on_click=lambda e, pid=proposal["id"]: view_proposal(pid),
                                    bgcolor=ft.colors.GREEN_600,
                                    color=ft.colors.WHITE,
                                    width=120
                                ),
                                ft.ElevatedButton(
                                    "Admin Review",
                                    icon=ft.icons.ADMIN_PANEL_SETTINGS,
                                    on_click=lambda e, pid=proposal["id"]: admin_review_proposal(pid),
                                    bgcolor=ft.colors.ORANGE_600,
                                    color=ft.colors.WHITE,
                                    width=120
                                ) if check_permission('all') else ft.Container(),
                                ft.ElevatedButton(
                                    "Delete",
                                    icon=ft.icons.DELETE,
                                    on_click=lambda e, pid=proposal["id"]: delete_proposal(pid),
                                    bgcolor=ft.colors.RED_700,
                                    color=ft.colors.WHITE,
                                    width=100
                                ) if check_permission('all') else ft.Container()
                            ], spacing=10)
                        ]),
                        padding=15
                    )
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Anonymous Proposals", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.ElevatedButton(
                            "Submit Proposal",
                            icon=ft.icons.ADD,
                            on_click=submit_anonymous_proposal,
                            bgcolor=ft.colors.BLUE_600,
                            color=ft.colors.WHITE
                        )
                    ], spacing=10)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=20),
                
                # Dynamic proposal items
                *proposal_cards
            ],
            spacing=10
            ),
            padding=20
        )
    
    def edit_bench(bench_id):
        """Show form to edit bench."""
        if not require_permission('write'):
            return
        try:
            bench = next(b for b in app_data.get("benches", []) if b["id"] == bench_id)
            show_bench_form(bench)
        except StopIteration:
            show_snackbar(f"Bench #{bench_id} not found!")
    
    def delete_bench(bench_id):
        """Delete bench."""
        if not require_permission('write'):
            return
        bench = next((b for b in app_data.get("benches", []) if b["id"] == bench_id), None)
        if bench:
            add_activity("Bench", f"Deleted bench: {bench['name']}", bench_id)
        
        if "benches" in app_data:
            app_data["benches"] = [b for b in app_data["benches"] if b["id"] != bench_id]
        secure_db.save_app_data(app_data)
        show_snackbar(f"Bench #{bench_id} deleted successfully!")
        refresh_current_tab()
    
    # Knowledge Share Functions
    def create_knowledge_content():
        """Create Facebook-style knowledge sharing feed."""
        return create_social_feed()
    
    def create_social_feed():
        """Create social media style feed for knowledge sharing."""
        # Create new post section
        new_post_field = ft.TextField(
            hint_text="What knowledge would you like to share?",
            multiline=True,
            max_lines=4,
            width=650,
            border_radius=10
        )
        
        # Create feed posts
        feed_posts = []
        
        for article in sorted(app_data.get("knowledge_articles", []), key=lambda x: x.get("timestamp", x.get("created_date", "")), reverse=True):
            # Check if current user liked this post
            user_id = current_user.username if current_user else "anonymous"
            user_liked = user_id in article.get("likes", [])
            
            # Create tags display
            tag_chips = []
            for tag in article.get("tags", []):
                tag_chips.append(
                    ft.Container(
                        content=ft.Text(f"#{tag}", size=12, color=ft.colors.BLUE_700),
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        bgcolor=ft.colors.BLUE_50,
                        border_radius=12
                    )
                )
            
            # Create comments display (first few comments)
            comment_items = []
            comments = article.get("comments", [])
            for comment in comments[:3]:  # Show first 3 comments
                comment_items.append(
                    ft.Container(
                        content=ft.Row([
                            ft.CircleAvatar(
                                content=ft.Text(comment.get("author", "?")[0].upper(), size=12),
                                radius=15,
                                bgcolor=ft.colors.BLUE_300
                            ),
                            ft.Column([
                                ft.Row([
                                    ft.Text(comment.get("author", "Unknown"), size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text(format_time_ago(comment.get("date", "")), size=10, color=ft.colors.GREY_600)
                                ], spacing=5),
                                ft.Text(comment.get("content", ""), size=12)
                            ], spacing=2, expand=True)
                        ], spacing=10),
                        padding=ft.padding.symmetric(vertical=5)
                    )
                )
            
            # Comment input for this post
            comment_input = ft.TextField(
                hint_text="Write a comment...",
                width=500,
                height=35,
                border_radius=20,
                content_padding=ft.padding.symmetric(horizontal=12, vertical=8)
            )
            
            def post_comment(e, article_id=article["id"], input_field=comment_input):
                if not input_field.value:
                    return
                
                from datetime import datetime
                new_comment = {
                    "id": max([c.get("id", 0) for c in article.get("comments", [])], default=0) + 1,
                    "author": current_user.get_full_name() if current_user else "Anonymous",
                    "content": input_field.value,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                if "comments" not in article:
                    article["comments"] = []
                article["comments"].append(new_comment)
                
                secure_db.save_app_data(app_data)
                input_field.value = ""
                refresh_current_tab()
            
            def toggle_like(e, article_id=article["id"]):
                user_id = current_user.username if current_user else "anonymous"
                article_data = next((a for a in app_data.get("knowledge_articles", []) if a["id"] == article_id), None)
                if not article_data:
                    return
                
                if "likes" not in article_data:
                    article_data["likes"] = []
                
                if user_id in article_data["likes"]:
                    article_data["likes"].remove(user_id)
                else:
                    article_data["likes"].append(user_id)
                
                article_data["like_count"] = len(article_data["likes"])
                secure_db.save_app_data(app_data)
                refresh_current_tab()
            
            # Create the post card
            post_card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        # Post header
                        ft.Row([
                            ft.CircleAvatar(
                                content=ft.Text(article.get("author", "?")[0].upper(), size=16),
                                radius=20,
                                bgcolor=ft.colors.BLUE_600
                            ),
                            ft.Column([
                                ft.Text(article.get("author", "Unknown"), size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(format_time_ago(article.get("timestamp", article.get("created_date", ""))), 
                                       size=12, color=ft.colors.GREY_600)
                            ], spacing=0, expand=True),
                            ft.PopupMenuButton(
                                items=[
                                    ft.PopupMenuItem(text="Edit", on_click=lambda e, aid=article["id"]: edit_article(aid)),
                                    ft.PopupMenuItem(text="Delete", on_click=lambda e, aid=article["id"]: delete_article(aid))
                                ] if check_permission('write') else []
                            )
                        ], spacing=10),
                        
                        ft.Container(height=10),
                        
                        # Post content
                        ft.Text(article.get("title", ""), size=16, weight=ft.FontWeight.BOLD) if article.get("title") else ft.Container(),
                        ft.Text(article.get("content", "No content"), size=14),
                        
                        # Tags
                        ft.Container(height=10) if tag_chips else ft.Container(),
                        ft.Row(tag_chips, spacing=5, wrap=True) if tag_chips else ft.Container(),
                        
                        ft.Container(height=15),
                        
                        # Like and comment counts
                        ft.Row([
                            ft.Text(f"{article.get('like_count', 0)} likes", size=12, color=ft.colors.GREY_600),
                            ft.Text(f"{len(article.get('comments', []))} comments", size=12, color=ft.colors.GREY_600)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Divider(height=1),
                        
                        # Action buttons
                        ft.Row([
                            ft.TextButton(
                                content=ft.Row([
                                    ft.Icon(ft.icons.FAVORITE if user_liked else ft.icons.FAVORITE_BORDER, 
                                           color=ft.colors.RED if user_liked else ft.colors.GREY_600, size=20),
                                    ft.Text("Like", color=ft.colors.RED if user_liked else ft.colors.GREY_600)
                                ], spacing=5, tight=True),
                                on_click=lambda e, aid=article["id"]: toggle_like(e, aid)
                            ),
                            ft.TextButton(
                                content=ft.Row([
                                    ft.Icon(ft.icons.CHAT_BUBBLE_OUTLINE, color=ft.colors.GREY_600, size=20),
                                    ft.Text("Comment", color=ft.colors.GREY_600)
                                ], spacing=5, tight=True),
                                on_click=lambda e: comment_input.focus()
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                        
                        ft.Divider(height=1),
                        
                        # Comments section
                        ft.Column(comment_items, spacing=5) if comment_items else ft.Container(),
                        
                        # Show more comments link
                        ft.TextButton(
                            f"View all {len(comments)} comments",
                            on_click=lambda e, aid=article["id"]: view_all_comments(aid)
                        ) if len(comments) > 3 else ft.Container(),
                        
                        # Comment input
                        ft.Row([
                            ft.CircleAvatar(
                                content=ft.Text((current_user.get_full_name()[0] if current_user else "?").upper(), size=12),
                                radius=15,
                                bgcolor=ft.colors.GREY_400
                            ),
                            comment_input,
                            ft.IconButton(
                                icon=ft.icons.SEND,
                                on_click=lambda e, aid=article["id"], inp=comment_input: post_comment(e, aid, inp),
                                icon_color=ft.colors.BLUE_600
                            )
                        ], spacing=10)
                        
                    ], spacing=5),
                    padding=20
                ),
                margin=ft.margin.only(bottom=10)
            )
            
            feed_posts.append(post_card)
        
        def create_new_post(e):
            if not new_post_field.value:
                show_snackbar("Please write something to share!")
                return
            
            from datetime import datetime
            current_time = datetime.now()
            
            new_id = max([a["id"] for a in app_data.get("knowledge_articles", [])], default=0) + 1
            new_article = {
                "id": new_id,
                "title": "",  # No title for social posts
                "content": new_post_field.value,
                "author": current_user.get_full_name() if current_user else "Anonymous",
                "created_date": current_time.strftime("%Y-%m-%d"),
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "tags": [],
                "comments": [],
                "likes": [],
                "like_count": 0
            }
            
            if "knowledge_articles" not in app_data:
                app_data["knowledge_articles"] = []
            app_data["knowledge_articles"].append(new_article)
            
            add_activity("Knowledge", f"Shared: {new_post_field.value[:50]}{'...' if len(new_post_field.value) > 50 else ''}", new_id)
            secure_db.save_app_data(app_data)
            new_post_field.value = ""
            refresh_current_tab()
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Text("Knowledge Share", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                
                # New post section
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.CircleAvatar(
                                    content=ft.Text((current_user.get_full_name()[0] if current_user else "?").upper(), size=16),
                                    radius=20,
                                    bgcolor=ft.colors.BLUE_600
                                ),
                                new_post_field
                            ], spacing=10),
                            ft.Container(height=10),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Share Knowledge",
                                    icon=ft.icons.SHARE,
                                    on_click=create_new_post,
                                    bgcolor=ft.colors.BLUE_600,
                                    color=ft.colors.WHITE
                                )
                            ], alignment=ft.MainAxisAlignment.END)
                        ]),
                        padding=20
                    ),
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Feed posts
                ft.Column(feed_posts, spacing=10, scroll=ft.ScrollMode.AUTO)
            ], scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def view_all_comments(article_id):
        """Show all comments for an article in a dialog."""
        article = next((a for a in app_data.get("knowledge_articles", []) if a["id"] == article_id), None)
        if not article:
            show_snackbar("Article not found!")
            return
        
        comments = article.get("comments", [])
        
        comment_items = []
        for comment in comments:
            comment_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.CircleAvatar(
                            content=ft.Text(comment.get("author", "?")[0].upper(), size=12),
                            radius=15,
                            bgcolor=ft.colors.GREY_400
                        ),
                        ft.Column([
                            ft.Row([
                                ft.Text(comment.get("author", "Unknown"), size=12, weight=ft.FontWeight.BOLD),
                                ft.Text(format_time_ago(comment.get("date", "")), size=10, color=ft.colors.GREY_600)
                            ], spacing=5),
                            ft.Text(comment.get("content", ""), size=12)
                        ], spacing=2, expand=True)
                    ], spacing=10),
                    padding=ft.padding.symmetric(vertical=5)
                )
            )
        
        def close_comments_dialog(e):
            page.dialog.open = False
            page.update()
        
        # Create comments dialog
        comments_dialog = ft.AlertDialog(
            title=ft.Text(f"All Comments ({len(comments)})", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    comment_items if comment_items else [ft.Text("No comments yet.", color=ft.colors.GREY_600)],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10
                ),
                width=500,
                height=400
            ),
            actions=[
                ft.TextButton("Close", on_click=close_comments_dialog)
            ]
        )
        
        page.dialog = comments_dialog
        comments_dialog.open = True
        page.update()
    
    def format_time_ago(timestamp):
        """Format timestamp to show time ago (e.g., '2 hours ago')."""
        if not timestamp:
            return "Unknown time"
        
        try:
            from datetime import datetime
            if isinstance(timestamp, str):
                if " " in timestamp:
                    post_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                else:
                    post_time = datetime.strptime(timestamp, "%Y-%m-%d")
            else:
                return str(timestamp)
            
            now = datetime.now()
            diff = now - post_time
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
        except:
            return timestamp
    
    def create_proposals_content():
        """Create anonymous proposals content with CRUD operations."""
        proposals = app_data.get("anonymous_proposals", [])
        
        def submit_proposal(e):
            """Show dialog for submitting a new anonymous proposal."""
            title_field = ft.TextField(label="Proposal Title", width=400)
            description_field = ft.TextField(
                label="Description",
                multiline=True,
                min_lines=3,
                max_lines=8,
                width=400
            )
            category_dropdown = ft.Dropdown(
                label="Category",
                width=400,
                options=[
                    ft.dropdown.Option("Process Improvement"),
                    ft.dropdown.Option("Technology"),
                    ft.dropdown.Option("Team Culture"),
                    ft.dropdown.Option("Training"),
                    ft.dropdown.Option("Infrastructure"),
                    ft.dropdown.Option("Other")
                ]
            )
            
            def save_proposal(e):
                if not title_field.value or not description_field.value or not category_dropdown.value:
                    show_snackbar("Please fill in all fields!")
                    return
                
                from datetime import datetime
                new_id = max([p["id"] for p in proposals], default=0) + 1
                new_proposal = {
                    "id": new_id,
                    "title": title_field.value,
                    "description": description_field.value,
                    "category": category_dropdown.value,
                    "status": "Pending Review",
                    "submitted_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "admin_response": "",
                    "response_date": ""
                }
                
                if "anonymous_proposals" not in app_data:
                    app_data["anonymous_proposals"] = []
                app_data["anonymous_proposals"].append(new_proposal)
                
                add_activity("Proposals", f"New proposal: {title_field.value}", new_id)
                secure_db.save_app_data(app_data)
                
                page.dialog.open = False
                page.update()
                refresh_current_tab()
                show_snackbar("✅ Proposal submitted successfully!")
            
            def cancel_dialog(e):
                page.dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Submit Anonymous Proposal", size=20, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column([
                        title_field,
                        description_field,
                        category_dropdown,
                        ft.Container(height=10),
                        ft.Text("Your proposal will remain anonymous and will be reviewed by administrators.",
                               size=12, color=ft.colors.GREY_600, italic=True)
                    ], spacing=10),
                    width=450,
                    height=300
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel_dialog),
                    ft.ElevatedButton("Submit Proposal", on_click=save_proposal, bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE)
                ]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        def respond_to_proposal(proposal_id):
            """Admin function to respond to a proposal."""
            if not check_permission('write'):
                show_snackbar("You don't have permission to respond to proposals!")
                return
            
            proposal = next((p for p in proposals if p["id"] == proposal_id), None)
            if not proposal:
                show_snackbar("Proposal not found!")
                return
            
            response_field = ft.TextField(
                label="Admin Response",
                multiline=True,
                min_lines=3,
                max_lines=8,
                width=400,
                value=proposal.get("admin_response", "")
            )
            status_dropdown = ft.Dropdown(
                label="Status",
                width=400,
                value=proposal.get("status", "Pending Review"),
                options=[
                    ft.dropdown.Option("Pending Review"),
                    ft.dropdown.Option("Under Consideration"),
                    ft.dropdown.Option("Approved"),
                    ft.dropdown.Option("Implemented"),
                    ft.dropdown.Option("Rejected")
                ]
            )
            
            def save_response(e):
                from datetime import datetime
                proposal["admin_response"] = response_field.value
                proposal["status"] = status_dropdown.value
                proposal["response_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                add_activity("Proposals", f"Response to: {proposal['title']}", proposal_id)
                secure_db.save_app_data(app_data)
                
                page.dialog.open = False
                page.update()
                refresh_current_tab()
                show_snackbar("✅ Response saved successfully!")
            
            def cancel_response(e):
                page.dialog.open = False
                page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text(f"Respond to Proposal: {proposal['title']}", size=18, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Category: {proposal['category']}", size=14, color=ft.colors.GREY_700),
                        ft.Text(f"Submitted: {format_time_ago(proposal['submitted_date'])}", size=12, color=ft.colors.GREY_600),
                        ft.Container(height=10),
                        ft.Text("Description:", weight=ft.FontWeight.BOLD),
                        ft.Text(proposal['description'], size=12),
                        ft.Container(height=15),
                        response_field,
                        status_dropdown
                    ], spacing=5),
                    width=450,
                    height=400
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel_response),
                    ft.ElevatedButton("Save Response", on_click=save_response, bgcolor=ft.colors.GREEN_600, color=ft.colors.WHITE)
                ]
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        def delete_proposal(proposal_id):
            """Admin function to delete a proposal."""
            if not check_permission('write'):
                show_snackbar("You don't have permission to delete proposals!")
                return
            
            def confirm_delete(e):
                app_data["anonymous_proposals"] = [p for p in app_data["anonymous_proposals"] if p["id"] != proposal_id]
                add_activity("Proposals", f"Deleted proposal ID: {proposal_id}", proposal_id)
                secure_db.save_app_data(app_data)
                
                page.dialog.open = False
                page.update()
                refresh_current_tab()
                show_snackbar("✅ Proposal deleted successfully!")
            
            def cancel_delete(e):
                page.dialog.open = False
                page.update()
            
            confirm_dialog = ft.AlertDialog(
                title=ft.Text("Confirm Delete", size=18, weight=ft.FontWeight.BOLD),
                content=ft.Text("Are you sure you want to delete this proposal? This action cannot be undone."),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel_delete),
                    ft.ElevatedButton("Delete", on_click=confirm_delete, bgcolor=ft.colors.RED_600, color=ft.colors.WHITE)
                ]
            )
            
            page.dialog = confirm_dialog
            confirm_dialog.open = True
            page.update()
        
        # Create proposal cards
        proposal_cards = []
        for proposal in proposals:
            # Status color mapping
            status_colors = {
                "Pending Review": ft.colors.ORANGE_600,
                "Under Consideration": ft.colors.BLUE_600,
                "Approved": ft.colors.GREEN_600,
                "Implemented": ft.colors.PURPLE_600,
                "Rejected": ft.colors.RED_600
            }
            
            status_color = status_colors.get(proposal["status"], ft.colors.GREY_600)
            
            # Admin action buttons (only for admins)
            admin_actions = []
            if check_permission('write'):
                admin_actions = [
                    ft.Container(height=10),
                    ft.Row([
                        ft.ElevatedButton(
                            "Respond",
                            icon=ft.icons.REPLY,
                            on_click=lambda e, pid=proposal["id"]: respond_to_proposal(pid),
                            bgcolor=ft.colors.BLUE_600,
                            color=ft.colors.WHITE,
                            height=35
                        ),
                        ft.ElevatedButton(
                            "Delete",
                            icon=ft.icons.DELETE,
                            on_click=lambda e, pid=proposal["id"]: delete_proposal(pid),
                            bgcolor=ft.colors.RED_600,
                            color=ft.colors.WHITE,
                            height=35
                        )
                    ], spacing=10)
                ]
            
            proposal_card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        # Header with status
                        ft.Row([
                            ft.Text(proposal["title"], size=16, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Container(
                                content=ft.Text(proposal["status"], size=12, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
                                bgcolor=status_color,
                                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                border_radius=12
                            )
                        ]),
                        
                        ft.Container(height=5),
                        
                        # Metadata
                        ft.Row([
                            ft.Text(f"Category: {proposal['category']}", size=12, color=ft.colors.GREY_700),
                            ft.Text(f"Submitted: {format_time_ago(proposal['submitted_date'])}", size=12, color=ft.colors.GREY_600)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Container(height=10),
                        
                        # Description
                        ft.Text(proposal["description"], size=14),
                        
                        # Admin response (if exists)
                        ft.Container(
                            content=ft.Column([
                                ft.Container(height=10),
                                ft.Text("Admin Response:", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(proposal["admin_response"], size=13, color=ft.colors.GREY_800),
                                ft.Text(f"Response Date: {format_time_ago(proposal['response_date'])}", 
                                       size=11, color=ft.colors.GREY_600)
                            ]),
                            visible=bool(proposal.get("admin_response"))
                        ),
                        
                        # Admin actions
                        ft.Column(admin_actions)
                        
                    ], spacing=5),
                    padding=20
                ),
                margin=ft.margin.only(bottom=10)
            )
            
            proposal_cards.append(proposal_card)
        
        # Empty state
        if not proposal_cards:
            proposal_cards = [ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.LIGHTBULB_OUTLINE, size=64, color=ft.colors.GREY_400),
                    ft.Text("No proposals yet", size=18, color=ft.colors.GREY_600),
                    ft.Text("Be the first to submit an anonymous proposal!", size=14, color=ft.colors.GREY_500)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                height=200
            )]
        
        return ft.Container(
            content=ft.Column([
                # Header with submit button
                ft.Row([
                    ft.Text("Anonymous Proposals", size=24, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(
                        "Submit Proposal",
                        icon=ft.icons.ADD,
                        on_click=submit_proposal,
                        bgcolor=ft.colors.BLUE_600,
                        color=ft.colors.WHITE
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=20),
                
                # Info text
                ft.Container(
                    content=ft.Text(
                        "💡 Submit anonymous suggestions and proposals for process improvements, new technologies, or any ideas to enhance our work environment. All submissions remain completely anonymous.",
                        size=14,
                        color=ft.colors.GREY_700
                    ),
                    padding=ft.padding.all(15),
                    bgcolor=ft.colors.BLUE_50,
                    border_radius=8,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Proposals list
                ft.Column(proposal_cards, scroll=ft.ScrollMode.AUTO)
            ], scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def refresh_from_database(e=None):
        """Refresh UI by reloading data from database."""
        global app_data
        try:
            
            loaded_data = secure_db.load_app_data()
            
            if loaded_data:
                app_data = loaded_data
            else:
                # Database is empty, use minimal empty structure
                app_data = {
                    "handovers": [],
                    "requirements": [],
                    "issues": [],
                    "test_suites": [],
                    "benches": [],
                    "knowledge_articles": [],
                    "anonymous_proposals": [],
                    "recent_activities": [],
                    "theme_mode": ft.ThemeMode.LIGHT
                }
            
            # Calculate total records for feedback
            total_records = sum(len(app_data.get(key, [])) for key in ["handovers", "requirements", "issues", "test_suites"])
            
            # Refresh all UI components
            refresh_current_tab()
            
            # Provide feedback
            show_snackbar(f"✅ Data refreshed from database! ({total_records} total records)")
            
        except Exception as ex:
            print(f"Error refreshing from database: {ex}")
            show_snackbar(f"❌ Failed to refresh data: {str(ex)}")
    
    def refresh_current_tab():
        """Refresh the current tab content."""
        try:
            # Get reference to the global tabs
            global main_tabs
            
            # Check if main_tabs exists and is accessible
            if 'main_tabs' not in globals() or main_tabs is None:
                show_main_app()
                return
            
            # Update all tab contents - especially important for dashboard
            main_tabs.tabs[0].content = create_dashboard_content()
            main_tabs.tabs[1].content = create_handovers_content() 
            main_tabs.tabs[2].content = create_requirements_content()
            main_tabs.tabs[3].content = create_issues_content()
            main_tabs.tabs[4].content = create_test_suites_content()
            main_tabs.tabs[5].content = create_benches_content()
            main_tabs.tabs[6].content = create_knowledge_content()
            main_tabs.tabs[7].content = create_proposals_content()
            
            # Update user management tab if it exists (for admins)
            if len(main_tabs.tabs) > 8 and check_permission('all'):
                main_tabs.tabs[8].content = create_users_content()
            
            # Update notification badge
            update_notification_badge()
            
            # Force update the page
            page.update()
            
        except Exception as e:
            print(f"Error refreshing tabs: {e}")
            try:
                show_main_app()
            except Exception as fallback_error:
                print(f"Fallback failed: {fallback_error}")
                show_snackbar("Data updated! Please switch tabs to see changes.")
    
    def show_main_app():
        """Show main application with navigation tabs."""
        page.clean()
        
        # Store reference to tabs for refreshing
        global main_tabs
        
        # Create user menu items based on permissions
        user_menu_items = [
            ft.PopupMenuItem(text="Profile", on_click=lambda e: auth_manager.show_user_profile_dialog(current_user)),
            ft.PopupMenuItem(text="Change Password", on_click=lambda e: auth_manager.show_change_password_dialog()),
        ]
        
        # Add admin-only options
        if check_permission('all'):
            user_menu_items.extend([
                ft.PopupMenuItem(),  # Divider
                ft.PopupMenuItem(text="User Management", on_click=lambda e: show_user_management_dialog()),
                ft.PopupMenuItem(text="Send Notifications", on_click=lambda e: show_notification_dialog()),
            ])
        
        user_menu_items.extend([
            ft.PopupMenuItem(),  # Divider
            ft.PopupMenuItem(text="Logout", on_click=lambda e: logout_user())
        ])
        
        # Create export menu items based on permissions
        export_menu_items = []
        if check_permission('export'):
            export_menu_items = [
                ft.PopupMenuItem(text="Export Handovers", on_click=lambda e: export_to_excel("Handovers")),
                ft.PopupMenuItem(text="Export Requirements", on_click=lambda e: export_to_excel("Requirements")),
                ft.PopupMenuItem(text="Export Issues", on_click=lambda e: export_to_excel("Issues")),
                ft.PopupMenuItem(text="Export Test Suites", on_click=lambda e: export_to_excel("Test Suites")),
                ft.PopupMenuItem(),  # Divider
            ]
        
        # Add admin-only database operations to export menu
        if check_permission('all'):
            export_menu_items.extend([
                ft.PopupMenuItem(),  # Divider
                ft.PopupMenuItem(text="💾 Backup Database", on_click=backup_data),
                ft.PopupMenuItem(text="🔄 Import Database", on_click=restore_database_from_backup),
                ft.PopupMenuItem(text="🗑️ Empty Database", on_click=clear_database),
            ])
        
        export_menu_items.extend([
            ft.PopupMenuItem(),  # Divider 
            ft.PopupMenuItem(text="Storage Stats", on_click=show_storage_stats),
            ft.PopupMenuItem(text="Settings", on_click=show_settings_dialog),
        ])
        
        # Create app bar with user-aware features
        page.appbar = ft.AppBar(
            title=ft.Text("BMS - Business Management System"),
            bgcolor=ft.colors.BLUE_GREY_800,
            color=ft.colors.WHITE,
            actions=[
                # User information display
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.PERSON, size=20),
                        ft.Text(f"Welcome, {current_user.get_full_name() if current_user else 'User'}!", size=14),
                        ft.Text(f"({current_user.role.title() if current_user else 'Unknown'})", size=12, color=ft.colors.WHITE70)
                    ], spacing=5),
                    padding=10
                ),
                ft.IconButton(
                    ft.icons.BRIGHTNESS_4 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.icons.BRIGHTNESS_7,
                    tooltip="Toggle theme",
                    on_click=toggle_theme
                ),
                ft.IconButton(
                    ft.icons.REFRESH,
                    tooltip="Refresh data from database",
                    on_click=refresh_from_database
                ),
                create_notification_button(),
                ft.PopupMenuButton(
                    items=export_menu_items,
                    tooltip="Export & Settings"
                ),
                ft.PopupMenuButton(
                    items=user_menu_items,
                    tooltip="User Menu",
                    icon=ft.icons.ACCOUNT_CIRCLE
                )
            ]
        )
        
        # Create navigation tabs
        main_tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Dashboard",
                    icon=ft.icons.DASHBOARD,
                    content=create_dashboard_content()
                ),
                ft.Tab(
                    text="Handovers",
                    icon=ft.icons.TRANSFER_WITHIN_A_STATION,
                    content=create_handovers_content()
                ),
                ft.Tab(
                    text="Requirements",
                    icon=ft.icons.ASSIGNMENT,
                    content=create_requirements_content()
                ),
                ft.Tab(
                    text="Issues",
                    icon=ft.icons.BUG_REPORT,
                    content=create_issues_content()
                ),
                ft.Tab(
                    text="Test Suites",
                    icon=ft.icons.PLAY_ARROW,
                    content=create_test_suites_content()
                ),
                ft.Tab(
                    text="Benches",
                    icon=ft.icons.COMPUTER,
                    content=create_benches_content()
                ),
                ft.Tab(
                    text="Knowledge",
                    icon=ft.icons.LIBRARY_BOOKS,
                    content=create_knowledge_content()
                ),
                ft.Tab(
                    text="Proposals",
                    icon=ft.icons.LIGHTBULB,
                    content=create_proposals_content()
                ),
            ] + ([ft.Tab(
                text="Users",
                icon=ft.icons.PEOPLE,
                content=create_users_content()
            )] if check_permission('all') else []), # Only show for admins
            expand=True
        )
        
        page.add(main_tabs)
        page.update()
    
    def create_dashboard_content():
        """Create dashboard tab content."""
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Dashboard Overview", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                
                # Dynamic Stats cards
                ft.Row([
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(str(len(app_data["handovers"])), size=32, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Handovers", size=14, color=ft.colors.WHITE70)
                            ], 
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5
                            ),
                            padding=20,
                            width=140,
                            height=90,
                            bgcolor=ft.colors.BLUE_600 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.BLUE_700,
                            border_radius=12
                        )
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(str(len(app_data["requirements"])), size=32, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Requirements", size=14, color=ft.colors.WHITE70)
                            ], 
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5
                            ),
                            padding=20,
                            width=140,
                            height=90,
                            bgcolor=ft.colors.GREEN_600 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.GREEN_700,
                            border_radius=12
                        )
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(str(len(app_data["issues"])), size=32, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Issues", size=14, color=ft.colors.WHITE70)
                            ], 
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5
                            ),
                            padding=20,
                            width=140,
                            height=90,
                            bgcolor=ft.colors.RED_600 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.RED_700,
                            border_radius=12
                        )
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(str(len(app_data["test_suites"])), size=32, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Test Suites", size=14, color=ft.colors.WHITE70)
                            ], 
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5
                            ),
                            padding=20,
                            width=140,
                            height=90,
                            bgcolor=ft.colors.ORANGE_600 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.ORANGE_700,
                            border_radius=12
                        )
                    )
                ], 
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                spacing=10
                ),
                
                # Second row of cards for new data types
                ft.Row([
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(str(len(app_data.get("benches", []))), size=32, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Benches", size=14, color=ft.colors.WHITE70)
                            ], 
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5
                            ),
                            padding=20,
                            width=140,
                            height=90,
                            bgcolor=ft.colors.PURPLE_600 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.PURPLE_700,
                            border_radius=12
                        )
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(str(len(app_data.get("knowledge_articles", []))), size=32, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Knowledge", size=14, color=ft.colors.WHITE70)
                            ], 
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5
                            ),
                            padding=20,
                            width=140,
                            height=90,
                            bgcolor=ft.colors.INDIGO_600 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.INDIGO_700,
                            border_radius=12
                        )
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(str(len(app_data.get("anonymous_proposals", []))), size=32, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                ft.Text("Proposals", size=14, color=ft.colors.WHITE70)
                            ], 
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5
                            ),
                            padding=20,
                            width=140,
                            height=90,
                            bgcolor=ft.colors.TEAL_600 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.TEAL_700,
                            border_radius=12
                        )
                    ),
                    ft.Container(width=140)  # Empty space to balance the row
                ], 
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                spacing=10
                ),
                
                ft.Container(height=30),
                
                # Recent Activities Section
                ft.Text("Recent Activities", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                create_recent_activities_section(),
                
                ft.Container(height=20),
                ft.Text("✅ Welcome to BMS Dashboard!", size=16, color=ft.colors.GREEN_700)
            ],
            spacing=10
            ),
            padding=20
        )
    
    def create_recent_activities_section():
        """Create recent activities section for dashboard."""
        
        if not app_data["recent_activities"]:
            return ft.Container(
                content=ft.Text(
                    "No recent activities. Start by creating handovers, requirements, issues, or test suites!",
                    size=14,
                    color=ft.colors.GREY_600 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.GREY_400,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=20,
                bgcolor=ft.colors.GREY_100 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.GREY_800,
                border_radius=8
            )
        
        activity_items = []
        
        for activity in app_data["recent_activities"][:5]:  # Show last 5 activities
            # Choose icon and color based on activity type
            icon_map = {
                "Handover": (ft.icons.TRANSFER_WITHIN_A_STATION, ft.colors.BLUE_600),
                "Requirement": (ft.icons.ASSIGNMENT, ft.colors.GREEN_600),
                "Issue": (ft.icons.BUG_REPORT, ft.colors.RED_600),
                "Test Suite": (ft.icons.PLAY_ARROW, ft.colors.ORANGE_600)
            }
            
            if isinstance(activity, dict):
                icon, color = icon_map.get(activity.get("type"), (ft.icons.INFO, ft.colors.GREY_600))
            else:
                print("Warning: activity is not a dict:", activity)
                icon, color = ft.icons.INFO, ft.colors.GREY_600
            
            # Parse activity safely
            if isinstance(activity, dict):
                icon, color = icon_map.get(activity.get("type"), (ft.icons.INFO, ft.colors.GREY_600))
                ts = activity.get("timestamp", "")
                time_only = ts.split(" ")[1][:5] if ts else "??:??"
                description = activity.get("description", "")
                activity_type = activity.get("type", "Unknown")
            else:
                print("Warning: activity is not a dict:", activity)
                icon, color = ft.icons.INFO, ft.colors.GREY_600
                time_only = "??:??"
                description = "N/A"
                activity_type = "Unknown"
            
            # Append container safely
            activity_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, color=color, size=20),
                        ft.Column([
                            ft.Text(
                                description,
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color=ft.colors.BLACK if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.WHITE
                            ),
                            ft.Text(
                                f"{activity_type} • {time_only}",
                                size=12,
                                color=ft.colors.GREY_600 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.GREY_400
                            )
                        ], spacing=2, expand=True),
                    ], spacing=12),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    bgcolor=ft.colors.WHITE if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.GREY_800,
                    border_radius=8,
                    border=ft.border.all(
                        1,
                        ft.colors.GREY_300 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.GREY_600
                    )
                )
            )
            
        
        return ft.Container(
            content=ft.Column(activity_items, spacing=8),
            padding=12,
            bgcolor=ft.colors.GREY_50 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.GREY_900,
            border_radius=12,
            border=ft.border.all(1, ft.colors.GREY_200 if app_data["theme_mode"] == ft.ThemeMode.LIGHT else ft.colors.GREY_700)
        )
    
    def create_handovers_content():
        """Create handovers tab content with dynamic data."""
        handover_cards = []
        
        for handover in sorted(app_data["handovers"], key=lambda x: x["id"], reverse=True):
            status_color = {
                "Pending": ft.colors.YELLOW_100,
                "In Progress": ft.colors.ORANGE_100,
                "Completed": ft.colors.GREEN_100
            }.get(handover.get("status", "Pending"), ft.colors.GREY_100)
            
            handover_cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f"{handover.get('from_team', 'Unknown')} → {handover.get('to_team', 'Unknown')}", size=16, weight=ft.FontWeight.BOLD),
                                ft.Chip(label=ft.Text(handover.get("status", "Pending")), bgcolor=status_color)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(handover.get("description", "No description"), size=14),
                            ft.Text(f"Date: {handover.get('date', 'Unknown')}", size=12, color=ft.colors.GREY_600),
                            ft.Container(height=10),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Edit",
                                    icon=ft.icons.EDIT,
                                    on_click=lambda e, hid=handover["id"]: edit_handover(hid),
                                    bgcolor=ft.colors.BLUE_600,
                                    color=ft.colors.WHITE,
                                    width=120,
                                    height=36
                                ),
                                ft.ElevatedButton(
                                    "Delete",
                                    icon=ft.icons.DELETE,
                                    on_click=lambda e, hid=handover["id"]: delete_handover(hid),
                                    bgcolor=ft.colors.RED_700,
                                    color=ft.colors.WHITE,
                                    width=120,
                                    height=36
                                )
                            ], spacing=10)
                        ]),
                        padding=15
                    )
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Handovers Management", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.ElevatedButton(
                            "Export CSV",
                            icon=ft.icons.TABLE_CHART,
                            on_click=lambda e: export_to_excel("Handovers"),
                            bgcolor=ft.colors.GREEN_600,
                            color=ft.colors.WHITE,
                            height=40
                        ),
                        ft.ElevatedButton(
                            "New Handover",
                            icon=ft.icons.ADD,
                            on_click=add_handover,
                            bgcolor=ft.colors.BLUE_600,
                            color=ft.colors.WHITE,
                            height=40
                        )
                    ], spacing=10)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=20),
                
                # Dynamic handover items
                *handover_cards
            ],
            spacing=10
            ),
            padding=20
        )
    
    def create_requirements_content():
        """Create requirements tab content with dynamic data."""
        req_cards = []
        
        for req in sorted(app_data["requirements"], key=lambda x: x["id"], reverse=True):
            priority_colors = {
                "Low": ft.colors.GREEN_100,
                "Medium": ft.colors.YELLOW_100,
                "High": ft.colors.ORANGE_100,
                "Critical": ft.colors.RED_100
            }
            status_colors = {
                "New": ft.colors.BLUE_600,
                "In Development": ft.colors.ORANGE_600,
                "Completed": ft.colors.GREEN_600,
                "On Hold": ft.colors.GREY_600
            }
            
            req_cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(req.get("title", "Untitled"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Chip(label=ft.Text(f"{req.get('priority', 'Medium')} Priority"), bgcolor=priority_colors.get(req.get("priority", "Medium"), ft.colors.GREY_100))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(req.get("description", "No description"), size=14),
                            ft.Text(f"Status: {req.get('status', 'New')}", size=12, color=status_colors.get(req.get("status", "New"), ft.colors.GREY_600)),
                            ft.Container(height=10),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Edit",
                                    icon=ft.icons.EDIT,
                                    on_click=lambda e, rid=req["id"]: edit_requirement(rid),
                                    bgcolor=ft.colors.BLUE_600,
                                    color=ft.colors.WHITE,
                                    width=120,
                                    height=36
                                ),
                                ft.ElevatedButton(
                                    "Delete",
                                    icon=ft.icons.DELETE,
                                    on_click=lambda e, rid=req["id"]: delete_requirement(rid),
                                    bgcolor=ft.colors.RED_700,
                                    color=ft.colors.WHITE,
                                    width=120,
                                    height=36
                                )
                            ], spacing=10)
                        ]),
                        padding=15
                    )
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Requirements Tracking", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.ElevatedButton(
                            "Export CSV",
                            icon=ft.icons.TABLE_CHART,
                            on_click=lambda e: export_to_excel("Requirements"),
                            bgcolor=ft.colors.GREEN_600,
                            color=ft.colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "Add Requirement",
                            icon=ft.icons.ADD,
                            on_click=add_requirement,
                            bgcolor=ft.colors.BLUE_600,
                            color=ft.colors.WHITE
                        )
                    ], spacing=10)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=20),
                *req_cards
            ],
            spacing=10
            ),
            padding=20
        )
    
    def create_issues_content():
        """Create issues tab content with dynamic data."""
        issue_cards = []
        
        for issue in sorted(app_data["issues"], key=lambda x: x["id"], reverse=True):
            priority_colors = {
                "Low": ft.colors.BLUE_100,
                "Medium": ft.colors.YELLOW_100, 
                "High": ft.colors.ORANGE_100,
                "Critical": ft.colors.RED_200
            }
            status_colors = {
                "Open": ft.colors.RED_600,
                "In Progress": ft.colors.ORANGE_600,
                "Testing": ft.colors.BLUE_600,
                "Resolved": ft.colors.GREEN_600,
                "Closed": ft.colors.GREY_600
            }
            
            issue_cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(issue.get("title", "Untitled"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Chip(label=ft.Text(issue.get("priority", "Medium")), bgcolor=priority_colors.get(issue.get("priority", "Medium"), ft.colors.GREY_100))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(issue.get("description", "No description"), size=14),
                            ft.Text(f"Created by: {issue.get('created_by', 'Unknown')}", size=12, color=ft.colors.GREY_600),
                            ft.Text(f"Assigned to: {issue.get('assigned', 'Unassigned')}", size=12, color=ft.colors.BLUE_600),
                            ft.Text(f"Status: {issue.get('status', 'Open')}", size=12, color=status_colors.get(issue.get("status", "Open"), ft.colors.GREY_600)),
                            ft.Container(height=10),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Edit",
                                    icon=ft.icons.EDIT,
                                    on_click=lambda e, iid=issue["id"]: edit_issue(iid),
                                    bgcolor=ft.colors.BLUE_600,
                                    color=ft.colors.WHITE,
                                    width=120
                                ),
                                ft.ElevatedButton(
                                    "Delete",
                                    icon=ft.icons.DELETE,
                                    on_click=lambda e, iid=issue["id"]: delete_issue(iid),
                                    bgcolor=ft.colors.RED_700,
                                    color=ft.colors.WHITE,
                                    width=120
                                )
                            ], spacing=10)
                        ]),
                        padding=15
                    )
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Issues Tracking", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.ElevatedButton(
                            "Export CSV",
                            icon=ft.icons.TABLE_CHART,
                            on_click=lambda e: export_to_excel("Issues"),
                            bgcolor=ft.colors.GREEN_600,
                            color=ft.colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "Report Issue",
                            icon=ft.icons.BUG_REPORT,
                            on_click=add_issue,
                            bgcolor=ft.colors.RED_600,
                            color=ft.colors.WHITE
                        )
                    ], spacing=10)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=20),
                
                # Dynamic issue items
                *issue_cards
            ],
            spacing=10
            ),
            padding=20
        )
    
    def create_test_suites_content():
        """Create test suites tab content with dynamic data."""
        suite_cards = []
        
        for suite in sorted(app_data["test_suites"], key=lambda x: x["id"], reverse=True):
            status_colors = {
                "Not Run": ft.colors.GREY_100,
                "Running": ft.colors.BLUE_100,
                "Passed": ft.colors.GREEN_100,
                "Failed": ft.colors.RED_100
            }
            
            suite_cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(suite.get("name", "Unnamed Suite"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Row([
                                    ft.Chip(label=ft.Text(suite.get("type", "Smoke")), bgcolor=ft.colors.PURPLE_100),
                                    ft.Chip(label=ft.Text(suite.get("status", "Not Run")), bgcolor=status_colors.get(suite.get("status", "Not Run"), ft.colors.GREY_100))
                                ], spacing=5)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(f"Last run: {suite.get('last_run', 'Never')}", size=14),
                            ft.Text(f"Tests passed: {suite.get('passed', 0)}/{suite.get('total', 0)}", size=12, color=ft.colors.GREEN_600 if suite.get('passed', 0) == suite.get('total', 0) else ft.colors.RED_600),
                            ft.Text(f"Duration: {suite.get('duration', '0s')}", size=12, color=ft.colors.GREY_600),
                            ft.Container(height=10),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Run",
                                    icon=ft.icons.PLAY_ARROW,
                                    on_click=lambda e, sid=suite["id"]: run_test_suite(sid),
                                    bgcolor=ft.colors.GREEN_600,
                                    color=ft.colors.WHITE,
                                    width=120
                                ),
                                ft.ElevatedButton(
                                    "Edit",
                                    icon=ft.icons.EDIT,
                                    on_click=lambda e, sid=suite["id"]: edit_test_suite(sid),
                                    bgcolor=ft.colors.BLUE_600,
                                    color=ft.colors.WHITE,
                                    width=120
                                ),
                                ft.ElevatedButton(
                                    "Delete",
                                    icon=ft.icons.DELETE,
                                    on_click=lambda e, sid=suite["id"]: delete_test_suite(sid),
                                    bgcolor=ft.colors.RED_700,
                                    color=ft.colors.WHITE,
                                    width=120
                                )
                            ], spacing=10)
                        ]),
                        padding=15
                    )
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Test Suites Management", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.ElevatedButton(
                            "Export CSV",
                            icon=ft.icons.TABLE_CHART,
                            on_click=lambda e: export_to_excel("Test Suites"),
                            bgcolor=ft.colors.GREEN_600,
                            color=ft.colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "New Test Suite",
                            icon=ft.icons.ADD,
                            on_click=add_test_suite,
                            bgcolor=ft.colors.BLUE_600,
                            color=ft.colors.WHITE
                        )
                    ], spacing=10)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=20),
                
                # Dynamic test suite items
                *suite_cards
            ],
            spacing=10
            ),
            padding=20
        )
    
    def create_benches_content():
        """Create benches tab content with dynamic data."""
        bench_cards = []
        
        for bench in sorted(app_data.get("benches", []), key=lambda x: x["id"], reverse=True):
            status_colors = {
                "Available": ft.colors.GREEN_100,
                "Occupied": ft.colors.ORANGE_100,
                "Maintenance": ft.colors.RED_100,
                "Reserved": ft.colors.BLUE_100
            }
            
            bench_cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(bench.get("name", "Unnamed Bench"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Chip(label=ft.Text(bench.get("status", "Available")), bgcolor=status_colors.get(bench.get("status", "Available"), ft.colors.GREY_100))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(f"Assigned to: {bench.get('assigned_to', 'None')}", size=14),
                            ft.Text(f"Project: {bench.get('project', 'None')}", size=14, color=ft.colors.BLUE_600),
                            ft.Text(f"Last updated: {bench.get('last_updated', 'Unknown')}", size=12, color=ft.colors.GREY_600),
                            ft.Container(height=10),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Edit",
                                    icon=ft.icons.EDIT,
                                    on_click=lambda e, bid=bench["id"]: edit_bench(bid),
                                    bgcolor=ft.colors.BLUE_600,
                                    color=ft.colors.WHITE,
                                    width=120
                                ),
                                ft.ElevatedButton(
                                    "Delete",
                                    icon=ft.icons.DELETE,
                                    on_click=lambda e, bid=bench["id"]: delete_bench(bid),
                                    bgcolor=ft.colors.RED_700,
                                    color=ft.colors.WHITE,
                                    width=120
                                )
                            ], spacing=10)
                        ]),
                        padding=15
                    )
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Benches Management", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.ElevatedButton(
                            "Export CSV",
                            icon=ft.icons.TABLE_CHART,
                            on_click=lambda e: export_to_excel("Benches"),
                            bgcolor=ft.colors.GREEN_600,
                            color=ft.colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "Add Bench",
                            icon=ft.icons.ADD,
                            on_click=add_bench,
                            bgcolor=ft.colors.BLUE_600,
                            color=ft.colors.WHITE
                        )
                    ], spacing=10)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=20),
                
                # Dynamic bench items
                *bench_cards
            ],
            spacing=10
            ),
            padding=20
        )
    
    def create_users_content():
        """Create user management tab content."""
        if not check_permission('all'):
            return ft.Container(
                content=ft.Text(
                    "Access denied. Admin privileges required.",
                    size=18,
                    color=ft.colors.RED_600,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=20
            )
        
        try:
            users = auth_service.get_all_users()
        except Exception as e:
            return ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Error loading users",
                        size=18,
                        color=ft.colors.RED_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        str(e),
                        size=12,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ]),
                padding=20
            )
        
        user_cards = []
        
        for user in sorted(users, key=lambda x: x.created_at, reverse=True):
            status_colors = {
                'active': ft.colors.GREEN_100,
                'inactive': ft.colors.GREY_100,
                'pending_verification': ft.colors.ORANGE_100,
                'suspended': ft.colors.RED_100
            }
            
            role_colors = {
                'admin': ft.colors.PURPLE_600,
                'manager': ft.colors.BLUE_600,
                'user': ft.colors.GREEN_600,
                'viewer': ft.colors.GREY_600
            }
            
            user_cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(user.get_full_name(), size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"@{user.username}", size=14, color=ft.colors.BLUE_600),
                                    ft.Text(user.email, size=12, color=ft.colors.GREY_600)
                                ], spacing=2),
                                ft.Column([
                                    ft.Chip(
                                        label=ft.Text(user.role.title()),
                                        bgcolor=role_colors.get(user.role, ft.colors.GREY_600)
                                    ),
                                    ft.Chip(
                                        label=ft.Text(user.status.replace('_', ' ').title()),
                                        bgcolor=status_colors.get(user.status, ft.colors.GREY_100)
                                    )
                                ], spacing=5)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            
                            ft.Container(height=10),
                            
                            ft.Row([
                                ft.Text(f"Last Login: {user.last_login or 'Never'}", size=12, color=ft.colors.GREY_600),
                                ft.Text(f"Created: {user.created_at[:10] if user.created_at else 'Unknown'}", size=12, color=ft.colors.GREY_600)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            
                            ft.Container(height=10),
                            
                            ft.Row([
                                ft.ElevatedButton(
                                    "Edit",
                                    icon=ft.icons.EDIT,
                                    on_click=lambda e, u=user: edit_user_details(u),
                                    bgcolor=ft.colors.BLUE_600,
                                    color=ft.colors.WHITE,
                                    width=120
                                ),
                                ft.ElevatedButton(
                                    "Email",
                                    icon=ft.icons.EMAIL,
                                    on_click=lambda e, u=user: send_user_email_dialog(u),
                                    bgcolor=ft.colors.GREEN_600,
                                    color=ft.colors.WHITE,
                                    width=120
                                ),
                                ft.ElevatedButton(
                                    "Sessions",
                                    icon=ft.icons.SCHEDULE,
                                    on_click=lambda e, u=user: show_user_sessions(u),
                                    bgcolor=ft.colors.ORANGE_600,
                                    color=ft.colors.WHITE,
                                    width=130
                                ) if user.status == 'active' else ft.Container()
                            ], spacing=10)
                        ]),
                        padding=15
                    )
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("User Management", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.ElevatedButton(
                            "Send Notification",
                            icon=ft.icons.NOTIFICATIONS,
                            on_click=lambda e: show_notification_dialog(),
                            bgcolor=ft.colors.PURPLE_600,
                            color=ft.colors.WHITE
                        ),
                        ft.ElevatedButton(
                            "Export Users",
                            icon=ft.icons.DOWNLOAD,
                            on_click=lambda e: export_users_data(),
                            bgcolor=ft.colors.GREEN_600,
                            color=ft.colors.WHITE
                        )
                    ], spacing=10)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=20),
                
                ft.Row([
                    ft.Text(f"Total Users: {len(users)}", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Active: {len([u for u in users if u.status == 'active'])}", size=14, color=ft.colors.GREEN_600),
                    ft.Text(f"Pending: {len([u for u in users if u.status == 'pending_verification'])}", size=14, color=ft.colors.ORANGE_600),
                    ft.Text(f"Suspended: {len([u for u in users if u.status == 'suspended'])}", size=14, color=ft.colors.RED_600)
                ], spacing=20),
                
                ft.Container(height=20),
            ] + (user_cards if user_cards else [ft.Text("No users found", size=16, color=ft.colors.GREY_600)]),
            spacing=10
            ),
            padding=20
        )
    
    def edit_user_details(user: User):
        """Edit user details dialog."""
        def on_update(form_data):
            # In a real implementation, you would update the user in the database
            show_snackbar(f"User {user.username} would be updated with: {form_data}")
            
        auth_manager.show_user_profile_dialog(user, on_update)
    
    def send_user_email_dialog(user: User):
        """Send email to specific user."""
        def on_send(form_data):
            success = auth_service.send_notification(
                user_emails=[user.email],
                subject=form_data['subject'],
                message=form_data['message'],
                notification_type=form_data['notification_type']
            )
            
            if success:
                show_snackbar(f"Email sent to {user.email}!")
            else:
                show_snackbar("Failed to send email")
        
        auth_manager.show_notification_dialog(on_send)
    
    def show_user_sessions(user: User):
        """Show user session management dialog."""
        # Get user sessions
        sessions = auth_service.get_user_sessions(user.username)
        session_count = len(sessions)
        
        def close_session_dialog():
            session_dialog.open = False
            page.update()
        
        def terminate_session(session_token):
            """Terminate a specific session."""
            if auth_service.terminate_session(session_token):
                show_snackbar("Session terminated successfully")
                # Refresh the dialog
                close_session_dialog()
                show_user_sessions(user)  # Reopen with updated data
            else:
                show_snackbar("Failed to terminate session")
        
        def terminate_all_sessions():
            """Terminate all sessions for this user."""
            # Don't terminate current session if viewing own sessions
            except_token = current_session_token if user.username == current_user.username else None
            
            terminated = auth_service.terminate_all_user_sessions(user.username, except_token)
            if terminated > 0:
                show_snackbar(f"Terminated {terminated} session{'s' if terminated != 1 else ''}")
                close_session_dialog()
                if user.username == current_user.username and terminated > 0:
                    # If current user terminated their own sessions, show updated view
                    show_user_sessions(user)
            else:
                show_snackbar("No sessions to terminate")
        
        # Create session list
        session_items = []
        
        if not sessions:
            session_items.append(
                ft.Container(
                    content=ft.Text(
                        "No active sessions found", 
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
        else:
            for i, session in enumerate(sessions):
                # Determine if this is the current session
                is_current = (current_session_token == session['session_token'] and 
                             user.username == current_user.username)
                
                # Card styling based on session state
                card_color = ft.colors.GREEN_50 if is_current else None
                border_color = ft.colors.GREEN_600 if is_current else ft.colors.GREY_300
                
                session_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            # Session header
                            ft.Row([
                                ft.Row([
                                    ft.Icon(
                                        ft.icons.DEVICES, 
                                        color=ft.colors.GREEN_600 if is_current else ft.colors.GREY_600,
                                        size=20
                                    ),
                                    ft.Text(
                                        f"Session {i+1}" + (" (Current)" if is_current else ""),
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.GREEN_800 if is_current else ft.colors.BLACK
                                    )
                                ], spacing=8),
                                ft.Text(
                                    session['age'],
                                    size=12,
                                    color=ft.colors.GREY_600
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            
                            ft.Container(height=8),
                            
                            # Session details
                            ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.COMPUTER, size=16, color=ft.colors.BLUE_600),
                                    ft.Text(f"Device: {session['device_info']}", size=13)
                                ], spacing=8),
                                ft.Row([
                                    ft.Icon(ft.icons.LOCATION_ON, size=16, color=ft.colors.RED_600),
                                    ft.Text(f"IP: {session['ip_address']} ({session['location']})", size=13)
                                ], spacing=8),
                                ft.Row([
                                    ft.Icon(ft.icons.ACCESS_TIME, size=16, color=ft.colors.ORANGE_600),
                                    ft.Text(f"Started: {session['created_at']}", size=13)
                                ], spacing=8),
                                ft.Row([
                                    ft.Icon(ft.icons.SCHEDULE, size=16, color=ft.colors.PURPLE_600),
                                    ft.Text(f"Expires: {session['expires_at']}", size=13)
                                ], spacing=8)
                            ], spacing=4),
                            
                            ft.Container(height=10),
                            
                            # Action buttons
                            ft.Row([
                                ft.ElevatedButton(
                                    "Terminate",
                                    icon=ft.icons.LOGOUT,
                                    on_click=lambda e, token=session['session_token']: terminate_session(token),
                                    bgcolor=ft.colors.RED_600,
                                    color=ft.colors.WHITE,
                                    disabled=is_current,  # Don't allow terminating current session
                                    width=120
                                ),
                                ft.Text(
                                    "(Current session)" if is_current else "",
                                    size=12,
                                    color=ft.colors.GREEN_600,
                                    italic=True
                                )
                            ], spacing=10)
                        ]),
                        padding=15,
                        bgcolor=card_color
                    ),
                    elevation=2,
                    margin=ft.margin.only(bottom=10)
                )
                session_items.append(session_card)
        
        # Create session management dialog
        session_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.DEVICES_OTHER, color=ft.colors.BLUE_600),
                ft.Text(f"Sessions for {user.get_full_name()}", size=18, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    # Session summary
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"Active Sessions: {session_count}", size=16, weight=ft.FontWeight.BOLD),
                            ft.ElevatedButton(
                                "Terminate All",
                                icon=ft.icons.LOGOUT,
                                on_click=lambda e: terminate_all_sessions(),
                                bgcolor=ft.colors.RED_600,
                                color=ft.colors.WHITE,
                                disabled=session_count == 0
                            ) if session_count > 0 else ft.Container()
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.padding.only(bottom=15)
                    ),
                    ft.Divider(),
                    
                    # Scrollable session list
                    ft.Container(
                        content=ft.ListView(
                            controls=session_items,
                            expand=True,
                            spacing=5,
                            padding=ft.padding.only(top=10)
                        ),
                        height=400,  # Fixed height for scrollable area
                        expand=True
                    )
                ]),
                width=600,
                height=500
            ),
            actions=[
                ft.TextButton(
                    "Refresh",
                    icon=ft.icons.REFRESH,
                    on_click=lambda e: (close_session_dialog(), show_user_sessions(user))
                ),
                ft.TextButton(
                    "Close",
                    on_click=lambda e: close_session_dialog()
                )
            ]
        )
        
        page.dialog = session_dialog
        session_dialog.open = True
        page.update()
    
    def export_users_data():
        """Export users data to CSV."""
        try:
            users = auth_service.get_all_users()
            if not users:
                show_snackbar("No users to export")
                return
            
            # Create CSV content
            import csv
            import io
            from datetime import datetime
            
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            
            # Write header
            writer.writerow(['Username', 'Email', 'Full Name', 'Role', 'Status', 'Email Verified', 
                           'Last Login', 'Failed Login Attempts', 'Created At'])
            
            # Write user data
            for user in users:
                writer.writerow([
                    user.username,
                    user.email,
                    user.get_full_name(),
                    user.role,
                    user.status,
                    'Yes' if user.email_verified else 'No',
                    user.last_login or 'Never',
                    user.failed_login_attempts,
                    user.created_at
                ])
            
            # Save to file
            exports_dir = os.path.join(os.getcwd(), "exports")
            os.makedirs(exports_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"users_export_{timestamp}.csv"
            filepath = os.path.join(exports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_buffer.getvalue())
            
            show_snackbar(f"✅ Users exported successfully! ({len(users)} records)\nSaved to: exports/{filename}")
            
        except Exception as e:
            show_snackbar(f"❌ Export failed: {str(e)}")
    
    # Start with login page
    show_login()

async def run_app():
    """Run the Flet app with proper async handling."""
    try:
        await ft.app_async(target=main, view=ft.AppView.WEB_BROWSER)
    except KeyboardInterrupt:
        print("App interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        print("Cleaning up...")
        try:
            # Cleanup any remaining tasks (exclude current task)
            current = asyncio.current_task()
            tasks = [t for t in asyncio.all_tasks() if t is not current and not t.done()]
            if tasks:
                print(f"Cancelling {len(tasks)} remaining tasks...")
                for t in tasks:
                    t.cancel()
                # Wait for cancelled tasks with timeout
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=2.0
                )
            print("Cleanup completed")
        except asyncio.TimeoutError:
            print("Cleanup timeout - forcing exit")
        except Exception as cleanup_error:
            print(f"Cleanup error: {cleanup_error}")

if __name__ == "__main__":
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        print("Application interrupted")
    except RuntimeError as e:
        if "Event loop is closed" not in str(e):
            print(f"Runtime error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print("Application exiting...")
        sys.exit(0)
