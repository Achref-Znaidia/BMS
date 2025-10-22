"""
Security settings and management UI components.
"""

import flet as ft
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from ...config import SecurityConfig
from ...utils.compression import CompressionType

class SecurityManager:
    """Manager for security-related UI components."""
    
    def __init__(self, page: ft.Page, show_snackbar: Callable[[str], None]):
        self.page = page
        self.show_snackbar = show_snackbar
    
    def show_security_settings_dialog(self, current_settings: Dict[str, Any],
                                    on_save: Callable[[Dict[str, Any]], None] = None):
        """Show security settings dialog."""
        
        # Encryption settings
        encryption_enabled = ft.Checkbox(
            label="Enable Encryption",
            value=current_settings.get('encryption_enabled', SecurityConfig.ENABLE_ENCRYPTION)
        )
        
        password_field = ft.TextField(
            label="Encryption Password",
            password=True,
            can_reveal_password=True,
            width=400,
            value=current_settings.get('password', '')
        )
        
        # Compression settings
        compression_enabled = ft.Checkbox(
            label="Enable Compression",
            value=current_settings.get('compression_enabled', SecurityConfig.ENABLE_COMPRESSION)
        )
        
        compression_type_dropdown = ft.Dropdown(
            label="Compression Type",
            width=400,
            options=[
                ft.dropdown.Option(comp_type.value, comp_type.value.title())
                for comp_type in CompressionType
            ],
            value=current_settings.get('compression_type', SecurityConfig.DEFAULT_COMPRESSION_TYPE)
        )
        
        compression_level_slider = ft.Slider(
            label="Compression Level",
            min=1,
            max=9,
            divisions=8,
            value=current_settings.get('compression_level', SecurityConfig.COMPRESSION_LEVEL),
            width=400
        )
        
        # Backup settings
        backup_encryption = ft.Checkbox(
            label="Encrypt Backups",
            value=current_settings.get('backup_encryption', SecurityConfig.BACKUP_ENCRYPTION)
        )
        
        backup_compression = ft.Checkbox(
            label="Compress Backups",
            value=current_settings.get('backup_compression', SecurityConfig.BACKUP_COMPRESSION)
        )
        
        retention_days = ft.TextField(
            label="Backup Retention (Days)",
            width=200,
            value=str(current_settings.get('retention_days', SecurityConfig.BACKUP_RETENTION_DAYS)),
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        # Data integrity
        enable_checksums = ft.Checkbox(
            label="Enable Data Integrity Checks",
            value=current_settings.get('enable_checksums', SecurityConfig.ENABLE_CHECKSUMS)
        )
        
        verify_on_read = ft.Checkbox(
            label="Verify Integrity on Read",
            value=current_settings.get('verify_integrity_on_read', SecurityConfig.VERIFY_INTEGRITY_ON_READ)
        )
        
        def save_settings(e):
            try:
                settings = {
                    'encryption_enabled': encryption_enabled.value,
                    'password': password_field.value,
                    'compression_enabled': compression_enabled.value,
                    'compression_type': compression_type_dropdown.value,
                    'compression_level': int(compression_level_slider.value),
                    'backup_encryption': backup_encryption.value,
                    'backup_compression': backup_compression.value,
                    'retention_days': int(retention_days.value) if retention_days.value else 30,
                    'enable_checksums': enable_checksums.value,
                    'verify_integrity_on_read': verify_on_read.value
                }
                
                if on_save:
                    on_save(settings)
                self.close_dialog(dialog)
                self.show_snackbar("Security settings saved successfully!")
                
            except Exception as ex:
                self.show_snackbar(f"Error saving settings: {str(ex)}")
        
        def close_dialog(e):
            self.close_dialog(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Security Settings"),
            content=ft.Column([
                ft.Text("Encryption Settings", size=16, weight=ft.FontWeight.BOLD),
                encryption_enabled,
                password_field,
                ft.Divider(),
                
                ft.Text("Compression Settings", size=16, weight=ft.FontWeight.BOLD),
                compression_enabled,
                compression_type_dropdown,
                compression_level_slider,
                ft.Divider(),
                
                ft.Text("Backup Settings", size=16, weight=ft.FontWeight.BOLD),
                backup_encryption,
                backup_compression,
                retention_days,
                ft.Divider(),
                
                ft.Text("Data Integrity", size=16, weight=ft.FontWeight.BOLD),
                enable_checksums,
                verify_on_read,
            ], height=600, scroll=ft.ScrollMode.ADAPTIVE),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Save", on_click=save_settings),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_backup_dialog(self, on_backup: Callable[[], None] = None,
                          on_restore: Callable[[], None] = None):
        """Show backup management dialog."""
        
        backup_button = ft.ElevatedButton(
            "Create Backup",
            icon=ft.icons.BACKUP,
            on_click=lambda e: self._handle_backup(on_backup)
        )
        
        restore_button = ft.ElevatedButton(
            "Restore from Backup",
            icon=ft.icons.RESTORE,
            on_click=lambda e: self._handle_restore(on_restore)
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Backup Management"),
            content=ft.Column([
                ft.Text("Database Backup & Restore", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Create encrypted backups of your data or restore from existing backups."),
                ft.Container(height=20),
                ft.Row([
                    backup_button,
                    restore_button
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], height=200),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_password_change_dialog(self, on_change: Callable[[str], None] = None):
        """Show password change dialog."""
        
        current_password = ft.TextField(
            label="Current Password",
            password=True,
            can_reveal_password=True,
            width=400
        )
        
        new_password = ft.TextField(
            label="New Password",
            password=True,
            can_reveal_password=True,
            width=400
        )
        
        confirm_password = ft.TextField(
            label="Confirm New Password",
            password=True,
            can_reveal_password=True,
            width=400
        )
        
        def change_password(e):
            if not current_password.value:
                self.show_snackbar("Please enter current password")
                return
            
            if not new_password.value:
                self.show_snackbar("Please enter new password")
                return
            
            if new_password.value != confirm_password.value:
                self.show_snackbar("New passwords do not match")
                return
            
            if len(new_password.value) < 8:
                self.show_snackbar("Password must be at least 8 characters long")
                return
            
            if on_change:
                on_change(new_password.value)
            self.close_dialog(dialog)
            self.show_snackbar("Password changed successfully!")
        
        def close_dialog(e):
            self.close_dialog(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Change Password"),
            content=ft.Column([
                current_password,
                new_password,
                confirm_password,
                ft.Text("Password must be at least 8 characters long", size=12, color=ft.colors.GREY)
            ], height=250),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Change", on_click=change_password),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def show_security_status(self, security_status: Dict[str, Any]):
        """Show security status information."""
        
        status_items = []
        
        # Encryption status
        encryption_status = "Enabled" if security_status.get('encryption_enabled') else "Disabled"
        encryption_color = ft.colors.GREEN if security_status.get('encryption_enabled') else ft.colors.RED
        
        status_items.append(
            ft.ListTile(
                title=ft.Text("Encryption"),
                subtitle=ft.Text(encryption_status),
                trailing=ft.Icon(
                    ft.icons.LOCK if security_status.get('encryption_enabled') else ft.icons.LOCK_OPEN,
                    color=encryption_color
                )
            )
        )
        
        # Compression status
        compression_status = "Enabled" if security_status.get('compression_enabled') else "Disabled"
        compression_color = ft.colors.GREEN if security_status.get('compression_enabled') else ft.colors.ORANGE
        
        status_items.append(
            ft.ListTile(
                title=ft.Text("Compression"),
                subtitle=ft.Text(f"{compression_status} ({security_status.get('compression_type', 'none')})"),
                trailing=ft.Icon(
                    ft.icons.COMPRESS if security_status.get('compression_enabled') else ft.icons.EXPAND,
                    color=compression_color
                )
            )
        )
        
        # Last password change
        last_change = security_status.get('last_password_change', 'Never')
        status_items.append(
            ft.ListTile(
                title=ft.Text("Last Password Change"),
                subtitle=ft.Text(last_change),
                trailing=ft.Icon(ft.icons.SECURITY)
            )
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Security Status"),
            content=ft.Column([
                ft.Text("Current Security Configuration", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                *status_items
            ], height=300, scroll=ft.ScrollMode.ADAPTIVE),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.show_dialog(dialog)
    
    def _handle_backup(self, on_backup: Callable[[], None]):
        """Handle backup creation."""
        if on_backup:
            on_backup()
        self.show_snackbar("Backup created successfully!")
    
    def _handle_restore(self, on_restore: Callable[[], None]):
        """Handle backup restore."""
        if on_restore:
            on_restore()
        self.show_snackbar("Restore initiated. Please select backup file.")
    
    def show_dialog(self, dialog: ft.AlertDialog):
        """Show a dialog."""
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def close_dialog(self, dialog: ft.AlertDialog):
        """Close a dialog."""
        dialog.open = False
        self.page.update()
