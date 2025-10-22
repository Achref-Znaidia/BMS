"""
Ultra-simple test to see what exactly is displaying
"""

import flet as ft

def main(page: ft.Page):
    page.title = "BMS Test"
    
    # Add simple content
    page.add(ft.Text("Hello! Can you see this text?", size=20))
    page.add(ft.ElevatedButton("Test Button", on_click=lambda e: print("Button works!")))
    
    page.update()

if __name__ == "__main__":
    ft.app(target=main)