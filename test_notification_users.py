#!/usr/bin/env python3
"""
Test script to create sample users for testing notification user selection.
"""

import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.services.auth_service import AuthService
from src.services.email_service import EmailService

def create_sample_users():
    """Create sample users for testing notification features."""
    print("Creating sample users for notification testing...\n")
    
    # Initialize services
    email_service = EmailService()
    auth_service = AuthService(email_service=email_service)
    
    # Sample users to create
    sample_users = [
        {
            'username': 'john_doe',
            'email': 'john.doe@example.com',
            'password': 'password123',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1-555-0101',
            'verified': True
        },
        {
            'username': 'jane_smith',
            'email': 'jane.smith@example.com',
            'password': 'password123',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+1-555-0102',
            'verified': True
        },
        {
            'username': 'bob_wilson',
            'email': 'bob.wilson@example.com',
            'password': 'password123',
            'first_name': 'Bob',
            'last_name': 'Wilson',
            'phone': '+1-555-0103',
            'verified': False  # This user will be unverified
        },
        {
            'username': 'alice_johnson',
            'email': 'alice.johnson@example.com',
            'password': 'password123',
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'phone': '+1-555-0104',
            'verified': True
        },
        {
            'username': 'charlie_brown',
            'email': 'charlie.brown@example.com',
            'password': 'password123',
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'phone': '+1-555-0105',
            'verified': False  # This user will be unverified
        }
    ]
    
    created_count = 0
    verified_count = 0
    unverified_count = 0
    
    for user_data in sample_users:
        try:
            # Register the user
            success, message = auth_service.register_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                phone=user_data['phone']
            )
            
            if success:
                created_count += 1
                
                # If user should be verified, manually verify them
                if user_data['verified']:
                    # Get the user to access their verification token
                    users = auth_service.get_all_users()
                    new_user = next((u for u in users if u.username == user_data['username']), None)
                    
                    if new_user and new_user.email_verification_token:
                        verify_success, verify_message = auth_service.verify_email(new_user.email_verification_token)
                        if verify_success:
                            verified_count += 1
                            print(f"✅ Created and verified: {user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
                        else:
                            print(f"⚠️  Created but failed to verify: {user_data['first_name']} {user_data['last_name']} - {verify_message}")
                    else:
                        print(f"⚠️  Created but no verification token: {user_data['first_name']} {user_data['last_name']}")
                else:
                    unverified_count += 1
                    print(f"📧 Created (unverified): {user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
            else:
                if "already exists" in message:
                    print(f"⚪ Already exists: {user_data['first_name']} {user_data['last_name']}")
                else:
                    print(f"❌ Failed to create: {user_data['first_name']} {user_data['last_name']} - {message}")
                
        except Exception as e:
            print(f"❌ Error creating {user_data['first_name']} {user_data['last_name']}: {str(e)}")
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} new users")
    print(f"   Verified: {verified_count} users (can receive emails)")
    print(f"   Unverified: {unverified_count} users (inbox notifications only)")
    
    # Show all current users
    print(f"\n👥 All Users in System:")
    try:
        all_users = auth_service.get_all_users()
        verified_users = [u for u in all_users if u.email_verified]
        unverified_users = [u for u in all_users if not u.email_verified]
        
        print(f"\n✅ Verified Users ({len(verified_users)}):")
        for user in verified_users:
            print(f"   • {user.get_full_name()} ({user.username}) - {user.email}")
        
        print(f"\n📧 Unverified Users ({len(unverified_users)}):")
        for user in unverified_users:
            print(f"   • {user.get_full_name()} ({user.username}) - {user.email}")
        
    except Exception as e:
        print(f"❌ Error retrieving users: {str(e)}")
    
    print(f"\n🎯 Ready for notification testing!")
    print("Now you can:")
    print("1. Run the main app (python main.py)")
    print("2. Login as admin/admin123") 
    print("3. Go to Users tab")
    print("4. Click 'Send Notification' button")
    print("5. Test the new user selection feature!")
    print("\nFeatures to test:")
    print("• Select specific users to receive notifications")
    print("• See verified vs unverified users")
    print("• Use 'Select All' functionality")
    print("• Send notifications to custom user groups")

if __name__ == "__main__":
    create_sample_users()