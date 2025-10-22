"""
Test imports to see which ones are failing.
"""

print("Testing imports...")

try:
    print("1. Testing flet...")
    import flet as ft
    print("   ✓ Flet imported successfully")
except Exception as e:
    print(f"   ✗ Flet import failed: {e}")

try:
    print("2. Testing datetime...")
    from datetime import datetime
    print("   ✓ Datetime imported successfully")
except Exception as e:
    print(f"   ✗ Datetime import failed: {e}")

try:
    print("3. Testing src.models.user...")
    from src.models.user import User, UserRole, UserStatus
    print("   ✓ User models imported successfully")
except Exception as e:
    print(f"   ✗ User models import failed: {e}")

try:
    print("4. Testing src.services.auth_service...")
    from src.services.auth_service import AuthService
    print("   ✓ AuthService imported successfully")
except Exception as e:
    print(f"   ✗ AuthService import failed: {e}")

try:
    print("5. Testing src.services.email_service...")
    from src.services.email_service import EmailService
    print("   ✓ EmailService imported successfully")
except Exception as e:
    print(f"   ✗ EmailService import failed: {e}")

try:
    print("6. Testing src.ui.main_app...")
    from src.ui.main_app import BMSApp
    print("   ✓ BMSApp imported successfully")
except Exception as e:
    print(f"   ✗ BMSApp import failed: {e}")

print("Import test complete!")
