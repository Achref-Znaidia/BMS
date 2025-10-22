#!/usr/bin/env python3
"""
Simple verification that the notification system has scrolling.
"""

import os
import sys

# Add the project directory to Python path  
sys.path.insert(0, os.path.dirname(__file__))

from src.services.auth_service import AuthService
from src.services.email_service import EmailService

def verify_notifications():
    """Verify that notifications exist for testing."""
    print("Verifying notification system...")
    
    # Initialize services
    email_service = EmailService()
    auth_service = AuthService(email_service=email_service)
    
    # Check admin notifications
    notifications = auth_service.get_user_notifications("admin")
    print(f"Admin has {len(notifications)} notifications:")
    
    for i, notif in enumerate(notifications[:5], 1):  # Show first 5
        status = "✓ Read" if notif['read'] else "○ Unread"
        print(f"  {i}. [{status}] {notif['subject']}")
    
    if len(notifications) > 5:
        print(f"  ... and {len(notifications) - 5} more notifications")
    
    print(f"\n🎯 Status: {'✅ Ready for scroll testing!' if len(notifications) > 5 else '⚠️ Need more notifications for scroll testing'}")
    print("\nTo test scrolling:")
    print("1. Run: python main.py") 
    print("2. Login as admin/admin123")
    print("3. Click the notification bell icon")
    print("4. Verify that you can scroll through all notifications")
    print("5. The Close button should always be visible at the bottom")

if __name__ == "__main__":
    verify_notifications()