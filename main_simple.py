"""
Simplified main app that gradually adds functionality.
"""

import flet as ft
from datetime import datetime

def main(page: ft.Page):
    """Simplified BMS app."""
    page.title = "BMS - Business Management System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    # Simple state
    is_logged_in = False
    current_user = None
    
    def show_snackbar(message):
        """Show snackbar message."""
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        page.update()
    
    def show_login():
        """Show login page."""
        page.clean()
        
        def login_clicked(e):
            nonlocal is_logged_in, current_user
            username = username_field.value
            password = password_field.value
            
            if username == "admin" and password == "admin123":
                is_logged_in = True
                current_user = "admin"
                show_snackbar("Login successful! Welcome to BMS.")
                show_main_app()
            else:
                show_snackbar("Invalid credentials. Try admin/admin123")
        
        username_field = ft.TextField(label="Username", width=300, autofocus=True)
        password_field = ft.TextField(label="Password", password=True, width=300)
        
        # Centered layout
        page.add(ft.Container(
            content=ft.Column([
                ft.Text("BMS - Business Management System", size=32, weight=ft.FontWeight.BOLD, 
                       text_align=ft.TextAlign.CENTER),
                ft.Text("Please login to continue", size=16, text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                username_field,
                password_field,
                ft.Container(height=20),
                ft.ElevatedButton("Login", on_click=login_clicked, width=300),
                ft.Container(height=10),
                ft.Text("Use: admin / admin123", size=12, color=ft.colors.GREY, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        ))
        page.update()
    
    def show_main_app():
        """Show main application."""
        page.clean()
        
        # Create simple dashboard
        dashboard = ft.Column([
            ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
            ft.Text(f"Welcome, {current_user}!", size=16),
            ft.Container(height=20),
            ft.Row([
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("5", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("Handovers")
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        width=120, height=80, padding=10, bgcolor=ft.colors.BLUE_100
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("12", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("Requirements")
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        width=120, height=80, padding=10, bgcolor=ft.colors.GREEN_100
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("3", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("Issues")
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        width=120, height=80, padding=10, bgcolor=ft.colors.RED_100
                    )
                ),
            ]),
            ft.Container(height=40),
            ft.ElevatedButton("Logout", on_click=lambda e: show_login())
        ])
        
        page.add(dashboard)
        page.update()
    
    # Start with login
    show_login()

if __name__ == "__main__":
    ft.app(target=main)
