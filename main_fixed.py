"""
Fixed main entry point for BMS application.
"""

import flet as ft

def main(page: ft.Page):
    """Main application entry point."""
    page.title = "BMS - Business Management System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    def show_login():
        """Show login page."""
        page.clean()
        
        # Create login form
        username_field = ft.TextField(
            label="Username", 
            width=300,
            hint_text="Enter admin",
            autofocus=True
        )
        password_field = ft.TextField(
            label="Password", 
            password=True, 
            width=300,
            hint_text="Enter admin123"
        )
        
        def login_clicked(e):
            username = username_field.value or ""
            password = password_field.value or ""
            
            if username == "admin" and password == "admin123":
                show_main_app()
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Invalid credentials. Use admin/admin123"),
                    bgcolor=ft.colors.RED_400
                )
                page.snack_bar.open = True
                page.update()
        
        # Create login layout
        login_container = ft.Container(
            content=ft.Column([
                ft.Container(height=50),  # Top spacing
                ft.Text(
                    "BMS", 
                    size=48, 
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.colors.BLUE_700
                ),
                ft.Text(
                    "Business Management System", 
                    size=18, 
                    text_align=ft.TextAlign.CENTER,
                    color=ft.colors.GREY_600
                ),
                ft.Container(height=40),
                
                # Login form
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Login", size=24, weight=ft.FontWeight.BOLD),
                            ft.Container(height=20),
                            username_field,
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
                            ft.Text(
                                "Default: admin / admin123",
                                size=12,
                                color=ft.colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=40
                    ),
                    width=400
                ),
                
                ft.Container(height=50),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
        
        page.add(login_container)
        page.update()
    
    def show_main_app():
        """Show main application dashboard."""
        page.clean()
        
        # Simple dashboard
        page.add(
            ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("BMS Dashboard", size=28, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Logout", 
                            icon=ft.icons.LOGOUT,
                            on_click=lambda e: show_login()
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.all(20),
                    bgcolor=ft.colors.BLUE_50,
                    border_radius=10
                ),
                
                ft.Container(height=20),
                
                # Stats cards
                ft.Row([
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("5", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_600),
                                ft.Text("Handovers", size=14, color=ft.colors.GREY_600)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=20,
                            width=150,
                            height=100
                        )
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("12", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_600),
                                ft.Text("Requirements", size=14, color=ft.colors.GREY_600)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=20,
                            width=150,
                            height=100
                        )
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("3", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.RED_600),
                                ft.Text("Issues", size=14, color=ft.colors.GREY_600)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=20,
                            width=150,
                            height=100
                        )
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("8", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE_600),
                                ft.Text("Test Suites", size=14, color=ft.colors.GREY_600)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=20,
                            width=150,
                            height=100
                        )
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                
                ft.Container(height=30),
                
                ft.Text("🚧 Full features coming soon! This is a working prototype.", 
                       size=16, 
                       color=ft.colors.GREY_600,
                       text_align=ft.TextAlign.CENTER)
            ])
        )
        page.update()
    
    # Start with login page
    show_login()

if __name__ == "__main__":
    ft.app(target=main)