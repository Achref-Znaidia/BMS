"""
Authentication UI components for login, registration, and password management.
"""

import flet as ft
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime

from ...models.user import User, UserRole, UserStatus
from ...utils.validators import Validators
from ...config import ThemeConfig

class AuthManager:
    """Manager for authentication UI components."""
    
    def __init__(self, page: ft.Page, show_snackbar: Callable[[str], None]):
        self.page = page
        self.show_snackbar = show_snackbar
        self.current_user = None
        self.session_token = None
    
    def show_login_dialog(self, on_login: Callable[[str, str], None] = None):
        """Show login dialog."""
        
        username_field = ft.TextField(
            label="Username or Email",
            width=400,
            autofocus=True
        )
        
        password_field = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=400
        )
        
        remember_checkbox = ft.Checkbox(
            label="Remember me",
            value=False
        )
        
        def login_clicked(e):
            username = username_field.value
            password = password_field.value
            
            if not username or not password:
                self.show_snackbar("Please enter username and password")
                return
            
            if on_login:
                on_login(username, password)
        
        def show_register_dialog(e):
            self.close_dialog(dialog)
            self.show_register_dialog()
        
        def show_forgot_password_dialog(e):
            self.close_dialog(dialog)
            self.show_forgot_password_dialog()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Login to BMS"),
            content=ft.Column([
                username_field,
                password_field,
                remember_checkbox,
                ft.Row([
                    ft.TextButton("Forgot Password?", on_click=show_forgot_password_dialog),
                    ft.TextButton("Register", on_click=show_register_dialog),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], height=250),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton("Login", on_click=login_clicked),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_register_dialog(self, on_register: Callable[[Dict[str, str]], None] = None):
        """Show registration dialog."""
        
        username_field = ft.TextField(
            label="Username",
            width=400,
            autofocus=True
        )
        
        email_field = ft.TextField(
            label="Email",
            width=400
        )
        
        first_name_field = ft.TextField(
            label="First Name",
            width=400
        )
        
        last_name_field = ft.TextField(
            label="Last Name",
            width=400
        )
        
        password_field = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=400
        )
        
        confirm_password_field = ft.TextField(
            label="Confirm Password",
            password=True,
            can_reveal_password=True,
            width=400
        )
        
        phone_field = ft.TextField(
            label="Phone (Optional)",
            width=400
        )
        
        def register_clicked(e):
            form_data = {
                'username': username_field.value,
                'email': email_field.value,
                'first_name': first_name_field.value,
                'last_name': last_name_field.value,
                'password': password_field.value,
                'confirm_password': confirm_password_field.value,
                'phone': phone_field.value
            }
            
            # Validate form data
            errors = self._validate_registration_data(form_data)
            if errors:
                self.show_snackbar("Validation errors: " + "; ".join(errors))
                return
            
            if on_register:
                on_register(form_data)
        
        def show_login_dialog(e):
            self.close_dialog(dialog)
            self.show_login_dialog()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Register for BMS"),
            content=ft.Column([
                username_field,
                email_field,
                first_name_field,
                last_name_field,
                password_field,
                confirm_password_field,
                phone_field,
                ft.TextButton("Already have an account? Login", on_click=show_login_dialog)
            ], height=500, scroll=ft.ScrollMode.ADAPTIVE),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton("Register", on_click=register_clicked),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_forgot_password_dialog(self, on_reset: Callable[[str], None] = None):
        """Show forgot password dialog."""
        
        email_field = ft.TextField(
            label="Email Address",
            width=400,
            autofocus=True
        )
        
        def reset_clicked(e):
            email = email_field.value
            
            if not email:
                self.show_snackbar("Please enter your email address")
                return
            
            if '@' not in email:
                self.show_snackbar("Please enter a valid email address")
                return
            
            if on_reset:
                on_reset(email)
        
        def show_login_dialog(e):
            self.close_dialog(dialog)
            self.show_login_dialog()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Reset Password"),
            content=ft.Column([
                ft.Text("Enter your email address and we'll send you a password reset link."),
                email_field,
                ft.TextButton("Remember your password? Login", on_click=show_login_dialog)
            ], height=200),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton("Send Reset Link", on_click=reset_clicked),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_change_password_dialog(self, on_change: Callable[[str, str], None] = None):
        """Show change password dialog."""
        
        current_password_field = ft.TextField(
            label="Current Password",
            password=True,
            can_reveal_password=True,
            width=400,
            autofocus=True
        )
        
        new_password_field = ft.TextField(
            label="New Password",
            password=True,
            can_reveal_password=True,
            width=400
        )
        
        confirm_password_field = ft.TextField(
            label="Confirm New Password",
            password=True,
            can_reveal_password=True,
            width=400
        )
        
        def change_clicked(e):
            current_password = current_password_field.value
            new_password = new_password_field.value
            confirm_password = confirm_password_field.value
            
            if not current_password or not new_password:
                self.show_snackbar("Please fill in all fields")
                return
            
            if new_password != confirm_password:
                self.show_snackbar("New passwords do not match")
                return
            
            if len(new_password) < 8:
                self.show_snackbar("Password must be at least 8 characters long")
                return
            
            if on_change:
                on_change(current_password, new_password)
        
        def _muted_text_color() -> str:
            theme = 'dark' if (self.page and self.page.theme_mode == ft.ThemeMode.DARK) else 'light'
            return ThemeConfig.COMPONENT_COLORS.get(theme, {}).get('muted_text', '#90A4AE')

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Change Password"),
            content=ft.Column([
                current_password_field,
                new_password_field,
                confirm_password_field,
                ft.Text("Password must be at least 8 characters long", size=12, color=_muted_text_color())
            ], height=250),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton("Change Password", on_click=change_clicked),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_user_profile_dialog(self, user: User, on_update: Callable[[Dict[str, str]], None] = None):
        """Show user profile dialog."""
        
        username_field = ft.TextField(
            label="Username",
            width=400,
            value=user.username,
            read_only=True
        )
        
        email_field = ft.TextField(
            label="Email",
            width=400,
            value=user.email,
            read_only=True
        )
        
        first_name_field = ft.TextField(
            label="First Name",
            width=400,
            value=user.first_name
        )
        
        last_name_field = ft.TextField(
            label="Last Name",
            width=400,
            value=user.last_name
        )
        
        phone_field = ft.TextField(
            label="Phone",
            width=400,
            value=user.phone
        )
        
        role_field = ft.TextField(
            label="Role",
            width=400,
            value=user.role.title(),
            read_only=True
        )
        
        status_field = ft.TextField(
            label="Status",
            width=400,
            value=user.status.title(),
            read_only=True
        )
        
        def update_clicked(e):
            form_data = {
                'first_name': first_name_field.value,
                'last_name': last_name_field.value,
                'phone': phone_field.value
            }
            
            if on_update:
                on_update(form_data)
        
        def change_password_clicked(e):
            self.close_dialog(dialog)
            self.show_change_password_dialog()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("User Profile"),
            content=ft.Column([
                username_field,
                email_field,
                first_name_field,
                last_name_field,
                phone_field,
                role_field,
                status_field,
                ft.ElevatedButton("Change Password", on_click=change_password_clicked)
            ], height=400, scroll=ft.ScrollMode.ADAPTIVE),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton("Update Profile", on_click=update_clicked),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_notification_dialog(self, on_send: Callable[[Dict[str, str]], None] = None, 
                                users_list: List[User] = None):
        """Show notification sending dialog with user selection."""
        
        subject_field = ft.TextField(
            label="Subject",
            width=400,
            autofocus=True
        )
        
        message_field = ft.TextField(
            label="Message",
            multiline=True,
            width=400,
            max_lines=5
        )
        
        notification_type_dropdown = ft.Dropdown(
            label="Notification Type",
            width=400,
            options=[
                ft.dropdown.Option("info", "Information"),
                ft.dropdown.Option("success", "Success"),
                ft.dropdown.Option("warning", "Warning"),
                ft.dropdown.Option("error", "Error")
            ],
            value="info"
        )
        
        # User selection components
        selected_users = set()  # Track selected user IDs
        
        def select_all_users(e):
            """Select or deselect all users."""
            select_all = e.control.value
            selected_users.clear()
            
            if select_all:
                for user in users_list or []:
                    if user.email_verified:  # Only verified users
                        selected_users.add(user.id)
            
            # Update all checkboxes
            for control in user_checkboxes:
                if isinstance(control, ft.Checkbox):
                    control.value = select_all and control.data in selected_users
            
            update_recipient_count()
            self.page.update()
        
        def on_user_checkbox_change(e, user_id: str):
            """Handle individual user checkbox change."""
            if e.control.value:
                selected_users.add(user_id)
            else:
                selected_users.discard(user_id)
            
            # Update select all checkbox
            total_available = len([u for u in users_list or [] if u.email_verified])
            select_all_checkbox.value = len(selected_users) == total_available
            
            update_recipient_count()
            self.page.update()
        
        def update_recipient_count():
            """Update the recipient count display."""
            count = len(selected_users)
            recipient_count.value = f"Recipients: {count} user{'s' if count != 1 else ''} selected"
            recipient_count.color = ft.colors.WHITE70 if self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.GREY_600
        
        # Create user selection UI
        user_selection_content = []
        user_checkboxes = []
        
        if users_list:
            # Select all checkbox
            select_all_checkbox = ft.Checkbox(
                label="Select All Users",
                value=False,
                on_change=select_all_users
            )
            user_selection_content.append(select_all_checkbox)
            user_checkboxes.append(select_all_checkbox)
            
            # Recipient count with dynamic color
            def _get_muted_color():
                return ft.colors.WHITE70 if self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.GREY_600
            
            recipient_count = ft.Text("Recipients: 0 users selected", size=12, color=_get_muted_color())
            user_selection_content.append(recipient_count)
            
            user_selection_content.append(ft.Divider())
            
            # Individual user checkboxes
            verified_users = [u for u in users_list if u.email_verified]
            unverified_users = [u for u in users_list if not u.email_verified]
            
            if verified_users:
                user_selection_content.append(
                    ft.Text("Verified Users:", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700)
                )
                
                for user in verified_users:
                    checkbox = ft.Checkbox(
                        label=f"{user.get_full_name()} ({user.email})",
                        value=False,
                        data=user.id,  # Store user ID in data property
                        on_change=lambda e, uid=user.id: on_user_checkbox_change(e, uid)
                    )
                    user_selection_content.append(checkbox)
                    user_checkboxes.append(checkbox)
            
            if unverified_users:
                user_selection_content.append(ft.Container(height=10))
                user_selection_content.append(
                    ft.Text("Unverified Users (cannot receive emails):", 
                           size=12, color=ft.colors.WHITE70 if self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.GREY_600, italic=True)
                )
                
                for user in unverified_users:
                    user_selection_content.append(
                        ft.Text(
                            f"  • {user.get_full_name()} ({user.email})",
                            size=12, 
                            color=ft.colors.WHITE60 if self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.GREY_500
                        )
                    )
        else:
            user_selection_content.append(
                ft.Text("No users available", color=ft.colors.WHITE70 if self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.GREY_600)
            )
        
        def send_clicked(e):
            form_data = {
                'subject': subject_field.value,
                'message': message_field.value,
                'notification_type': notification_type_dropdown.value,
                'selected_user_ids': list(selected_users)
            }
            
            if not form_data['subject'] or not form_data['message']:
                self.show_snackbar("Please fill in subject and message")
                return
            
            if not selected_users:
                self.show_snackbar("Please select at least one user to send to")
                return
            
            if on_send:
                on_send(form_data)
        
        # Initialize with all users selected by default
        if users_list:
            for user in users_list:
                if user.email_verified:
                    selected_users.add(user.id)
            
            # Set initial values for checkboxes
            select_all_checkbox.value = len(selected_users) > 0
            
            # Update user checkboxes to reflect initial selection
            for checkbox in user_checkboxes:
                if isinstance(checkbox, ft.Checkbox) and hasattr(checkbox, 'data'):
                    checkbox.value = checkbox.data in selected_users
            
            update_recipient_count()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.SEND, color=ft.colors.BLUE_600),
                ft.Text("Send Notification", size=18, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    # Message composition section
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Message Details", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700),
                                ft.Container(height=10),
                                subject_field,
                                message_field,
                                notification_type_dropdown,
                            ], spacing=8),
                            padding=15
                        ),
                        elevation=2
                    ),
                    
                    ft.Container(height=15),
                    
                    # User selection section
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Select Recipients", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700),
                                ft.Container(height=10),
                                ft.Container(
                                    content=ft.Column(
                                        user_selection_content,
                                        scroll=ft.ScrollMode.AUTO,
                                        spacing=5
                                    ),
                                    height=180,
                                    border=ft.border.all(1, ft.colors.GREY_600 if self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.GREY_200),
                                    border_radius=8,
                                    padding=10,
                                    bgcolor=ft.colors.GREY_900 if self.page.theme_mode == ft.ThemeMode.DARK else ft.colors.GREY_50
                                )
                            ], spacing=5),
                            padding=15
                        ),
                        elevation=2
                    )
                ], 
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=10,
                expand=True
                ),
                width=600,  # Increased width for better content layout
                height=650,  # Slightly increased height
                padding=20
            ),
            actions=[
                ft.Row([
                    ft.TextButton(
                        "Cancel", 
                        on_click=lambda e: self.close_dialog(dialog),
                        icon=ft.icons.CANCEL
                    ),
                    ft.ElevatedButton(
                        "Send Notification", 
                        on_click=send_clicked,
                        icon=ft.icons.SEND,
                        bgcolor=ft.colors.BLUE_600,
                        color=ft.colors.WHITE
                    ),
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ],
        )
        
        self.show_dialog(dialog)
    
    def _validate_registration_data(self, data: Dict[str, str]) -> List[str]:
        """Validate registration form data."""
        errors = []
        
        if not data.get('username') or len(data['username']) < 3:
            errors.append("Username must be at least 3 characters")
        
        if not data.get('email') or '@' not in data['email']:
            errors.append("Please enter a valid email address")
        
        if not data.get('password') or len(data['password']) < 8:
            errors.append("Password must be at least 8 characters")
        
        if data.get('password') != data.get('confirm_password'):
            errors.append("Passwords do not match")
        
        return errors
    
    def create_user_info_display(self, user: User) -> ft.Container:
        """Create user information display for app bar."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.PERSON),
                ft.Text(user.get_full_name()),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="Profile", on_click=lambda e: self.show_user_profile_dialog(user)),
                        ft.PopupMenuItem(text="Change Password", on_click=lambda e: self.show_change_password_dialog()),
                        ft.PopupMenuItem(text="Logout", on_click=lambda e: self.logout())
                    ]
                )
            ]),
            padding=10
        )
    
    def logout(self):
        """Logout current user."""
        self.current_user = None
        self.session_token = None
        self.show_snackbar("Logged out successfully")
        # In a real app, you would redirect to login page
    
    def show_dialog(self, dialog: ft.AlertDialog):
        """Show a dialog."""
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def close_dialog(self, dialog: ft.AlertDialog):
        """Close a dialog."""
        dialog.open = False
        self.page.update()
