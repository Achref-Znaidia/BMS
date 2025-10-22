#!/usr/bin/env python3
"""
Debug script to understand the notification button structure.
"""

import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.services.auth_service import AuthService
from src.services.email_service import EmailService

def debug_notification_button():
    """Debug the notification button behavior."""
    print("🔧 Debugging Notification Button Structure\n")
    
    # Initialize services
    email_service = EmailService()
    auth_service = AuthService(email_service=email_service)
    
    # Test different unread counts
    print("Testing different notification counts:\n")
    
    # Simulate different unread counts
    test_counts = [0, 1, 5, 12, 99, 150]
    
    for count in test_counts:
        print(f"📊 Unread count: {count}")
        
        if count > 0:
            badge_text = str(count) if count < 100 else "99+"
            print(f"   Badge text: '{badge_text}'")
            print(f"   Button type: ft.Row (with IconButton + Container badge)")
            print(f"   Tooltip: 'View notifications ({count} unread)'")
        else:
            print(f"   Badge text: None (hidden)")
            print(f"   Button type: ft.IconButton")
            print(f"   Tooltip: 'View notifications'")
        
        print()
    
    print("🔍 Current system state:")
    notifications = auth_service.get_user_notifications("admin")
    total = len(notifications)
    unread = len([n for n in notifications if not n.get('read', False)])
    
    print(f"   Admin notifications: {total} total, {unread} unread")
    
    if unread > 0:
        badge_text = str(unread) if unread < 100 else "99+"
        print(f"   Current badge should show: '{badge_text}'")
        print(f"   Current button type: ft.Row")
    else:
        print(f"   Current badge should be: Hidden")
        print(f"   Current button type: ft.IconButton")
    
    print(f"\n🚨 Potential Issues:")
    print("1. Update function not finding the right button type")
    print("2. Button replacement creating duplicates instead of replacing")
    print("3. App bar actions list getting corrupted during updates")
    
    print(f"\n💡 Debug Steps:")
    print("1. Check app bar actions count before/after update")
    print("2. Print button types during update process")
    print("3. Verify button replacement is working correctly")
    
    print(f"\n🔧 Proposed Fix:")
    print("- Improve button identification logic")
    print("- Add logging to update process") 
    print("- Ensure only one notification button exists")

if __name__ == "__main__":
    debug_notification_button()