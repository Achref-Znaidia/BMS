"""
Ultra-simple test to check if Flet is working at all.
"""

import flet as ft
import warnings

# Suppress the asyncio warnings - this is a known issue with Flet 0.22.1
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Event loop is closed.*")

def main(page: ft.Page):
    page.title = "Simple Test"
    page.add(ft.Text("Hello World! Flet is working."))
    page.add(ft.ElevatedButton("Click me", on_click=lambda e: print("Button clicked!")))

if __name__ == "__main__":
    ft.app(target=main)
