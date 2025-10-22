"""
Debug version of main.py to identify where the UI fails to load.
"""

import flet as ft

def main(page: ft.Page):
    """Debug main entry point."""
    print("Debug main() called")
    
    try:
        print("Step 1: Setting up page...")
        page.title = "BMS Debug"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        print("Step 1: ✓ Page setup complete")
        
        print("Step 2: Testing basic UI...")
        page.add(ft.Text("Debug: If you can see this, basic UI works"))
        page.update()
        print("Step 2: ✓ Basic UI works")
        
        print("Step 3: Testing imports...")
        try:
            from src.ui.main_app import BMSApp
            print("Step 3a: ✓ BMSApp import works")
            
            app = BMSApp()
            print("Step 3b: ✓ BMSApp instantiation works")
            
            # Clear page and try to run the actual app
            print("Step 4: Running actual app...")
            page.clean()
            app.main(page)
            print("Step 4: ✓ App main() called")
            
        except Exception as e:
            print(f"Step 3/4: ✗ Error with BMSApp: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error on page
            page.clean()
            page.add(ft.Column([
                ft.Text("Import/Initialization Error", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(f"Error: {str(e)}", size=16),
                ft.Text("Check console for details", size=12)
            ]))
            page.update()
            
    except Exception as e:
        print(f"Debug main error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting debug version...")
    ft.app(target=main)