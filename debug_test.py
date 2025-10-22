"""
Debug test to see what's happening step by step.
"""

import flet as ft

def main(page: ft.Page):
    print("Starting debug test...")
    
    page.title = "Debug Test"
    print("Title set")
    
    page.theme_mode = ft.ThemeMode.LIGHT
    print("Theme set")
    
    page.padding = 20
    print("Padding set")
    
    # Add components one by one
    print("Adding title...")
    page.add(ft.Text("Debug Test - Step 1", size=24, weight=ft.FontWeight.BOLD))
    
    print("Adding subtitle...")
    page.add(ft.Text("If you can see this, Flet is working", size=16))
    
    print("Adding button...")
    def button_clicked(e):
        print("Button clicked!")
        page.snack_bar = ft.SnackBar(content=ft.Text("Button works!"))
        page.snack_bar.open = True
        page.update()
    
    page.add(ft.ElevatedButton("Test Button", on_click=button_clicked))
    
    print("Adding text field...")
    page.add(ft.TextField(label="Test Input", width=300))
    
    print("Calling page.update()...")
    page.update()
    print("Debug test complete!")

if __name__ == "__main__":
    print("Starting Flet app...")
    ft.app(target=main)
    print("Flet app finished")
