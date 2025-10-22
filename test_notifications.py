#!/usr/bin/env python3
"""
Test script for notification system functionality.
"""

import os
import sys
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.services.auth_service import AuthService
from src.services.email_service import EmailService

def test_notification_system():
    """Test the notification system."""
    print("Testing notification system...")
    
    # Initialize services
    email_service = EmailService()
    auth_service = AuthService(db_name="test_notifications.db", email_service=email_service)
    
    # Test user creation and notification
    print("\n1. Creating test user...")
    success, message = auth_service.register_user(
        username="testuser",
        email="test@example.com",
        password="password123",
        first_name="Test",
        last_name="User"
    )
    print(f"Registration: {success} - {message}")
    
    # Test creating notifications
    print("\n2. Creating notifications...")
    notif1 = auth_service.create_user_notification(
        username="testuser",
        subject="Welcome Message",
        message="Welcome to the system! This is your first notification.",
        notification_type="info"
    )
    
    notif2 = auth_service.create_user_notification(
        username="testuser", 
        subject="System Alert",
        message="This is an important system alert notification.",
        notification_type="alert"
    )
    
    print(f"Notification 1 created: {notif1}")
    print(f"Notification 2 created: {notif2}")
    
    # Test retrieving notifications
    print("\n3. Retrieving notifications...")
    notifications = auth_service.get_user_notifications("testuser")
    print(f"Retrieved {len(notifications)} notifications:")
    
    for i, notif in enumerate(notifications, 1):
        print(f"  {i}. {notif['subject']} - {notif['message'][:50]}... (Read: {notif['read']})")
    
    # Test marking as read
    if notifications:
        print(f"\n4. Marking first notification as read...")
        first_notif_id = notifications[0]['id']
        success = auth_service.mark_notification_read("testuser", first_notif_id)
        print(f"Mark as read result: {success}")
        
        # Retrieve again to verify
        updated_notifications = auth_service.get_user_notifications("testuser") 
        for notif in updated_notifications:
            if notif['id'] == first_notif_id:
                print(f"  First notification read status: {notif['read']}")
                break
    
    # Test deleting notification
    if len(notifications) > 1:
        print(f"\n5. Deleting second notification...")
        second_notif_id = notifications[1]['id']
        success = auth_service.delete_notification("testuser", second_notif_id)
        print(f"Delete result: {success}")
        
        # Retrieve again to verify
        final_notifications = auth_service.get_user_notifications("testuser")
        print(f"Notifications remaining: {len(final_notifications)}")
    
    print("\n✅ Notification system test completed!")
    
    # Clean up test database
    try:
        os.remove("test_notifications.db")
        print("✅ Test database cleaned up")
    except:
        pass

if __name__ == "__main__":
    test_notification_system()