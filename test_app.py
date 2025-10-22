"""
Simple test version of BMS app to verify basic functionality.
"""

import flet as ft

def main(page: ft.Page):
    """Simple test app."""
    page.title = "BMS Test"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    def login_clicked(e):
        username = username_field.value
        password = password_field.value
        
        if username == "admin" and password == "admin123":
            page.clean()
            page.add(ft.Text("Login successful! BMS is working.", size=24, weight=ft.FontWeight.BOLD))
            page.add(ft.Text("You can now run the full application with: python main.py"))
        else:
            page.snack_bar = ft.SnackBar(content=ft.Text("Invalid credentials. Try admin/admin123"))
            page.snack_bar.open = True
            page.update()
    
    # Create login form
    username_field = ft.TextField(label="Username", width=300)
    password_field = ft.TextField(label="Password", password=True, width=300)
    
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("BMS Test Application", size=32, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                ft.Text("Test Login (admin/admin123)", size=16, text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                username_field,
                password_field,
                ft.Container(height=20),
                ft.ElevatedButton("Login", on_click=login_clicked, width=300)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
