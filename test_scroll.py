#!/usr/bin/env python3
"""
Test script to create multiple notifications for testing scrolling.
"""

import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.services.auth_service import AuthService
from src.services.email_service import EmailService

def create_multiple_notifications():
    """Create multiple notifications for the admin user to test scrolling."""
    print("Creating multiple notifications for testing scrolling...")
    
    # Initialize services
    email_service = EmailService()
    auth_service = AuthService(email_service=email_service)
    
    # Create multiple notifications for admin user
    notifications = [
        ("Welcome to BMS!", "Welcome to the Business Management System. This is your introduction to the platform."),
        ("System Update", "The system has been updated with new notification features. Check them out!"),
        ("Security Alert", "Your password will expire in 30 days. Please update it in your profile settings."),
        ("New Feature Available", "We've added a new export feature for handovers. You can now export to CSV format."),
        ("Maintenance Notice", "System maintenance is scheduled for this weekend. Expect brief downtime."),
        ("Backup Complete", "Your data backup has been completed successfully. All data is secure."),
        ("User Registration", "A new user has registered and is pending approval. Check the user management tab."),
        ("Test Suite Update", "New test suites have been added to the system. Review them in the Test Suites tab."),
        ("Issue Resolved", "Issue #123 has been marked as resolved. Thank you for your patience."),
        ("Performance Report", "Monthly performance report is now available for download."),
        ("Training Session", "Mandatory training session scheduled for next week. Please confirm attendance."),
        ("Data Export Ready", "Your requested data export is ready for download. Check your email for the link."),
    ]
    
    created_count = 0
    for subject, message in notifications:
        if auth_service.create_user_notification(
            username="admin",
            subject=subject,
            message=message,
            notification_type="info"
        ):
            created_count += 1
            print(f"Created: {subject}")
    
    print(f"\n✅ Created {created_count} notifications for admin user")
    print("Now run the main app and login as admin/admin123 to test scrolling!")

if __name__ == "__main__":
    create_multiple_notifications()