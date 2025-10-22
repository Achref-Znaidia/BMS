#!/usr/bin/env python3
"""
Test script to create demo sessions for testing session management.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.services.auth_service import AuthService
from src.services.email_service import EmailService

def create_demo_sessions():
    """Create demo sessions for testing session management."""
    print("Creating demo sessions for testing session management...")
    
    # Initialize services
    email_service = EmailService()
    auth_service = AuthService(email_service=email_service)
    
    # Get admin user ID
    users = auth_service.get_all_users()
    admin_user = next((u for u in users if u.username == "admin"), None)
    
    if not admin_user:
        print("❌ Admin user not found!")
        return
    
    print(f"Creating sessions for admin user (ID: {admin_user.id})")
    
    # Create multiple demo sessions with different scenarios
    demo_sessions = [
        {
            'ip_address': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        {
            'ip_address': '192.168.1.101', 
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        {
            'ip_address': '10.0.0.50',
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        {
            'ip_address': '203.0.113.45',  # External IP
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
        },
        {
            'ip_address': '198.51.100.123',  # External IP
            'user_agent': 'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
        }
    ]
    
    created_sessions = []
    for i, session_data in enumerate(demo_sessions, 1):
        try:
            # Create session directly in database
            session = auth_service._create_session(
                user_id=admin_user.id,
                ip_address=session_data['ip_address'],
                user_agent=session_data['user_agent']
            )
            created_sessions.append(session)
            
            device_info = auth_service._parse_user_agent(session_data['user_agent'])
            location = auth_service._get_location_from_ip(session_data['ip_address'])
            
            print(f"  ✓ Session {i}: {device_info} from {session_data['ip_address']} ({location})")
            
        except Exception as e:
            print(f"  ❌ Failed to create session {i}: {e}")
    
    print(f"\n✅ Created {len(created_sessions)} demo sessions for admin user")
    
    # Show session summary
    sessions = auth_service.get_user_sessions("admin")
    print(f"📊 Admin now has {len(sessions)} active sessions:")
    
    for i, session in enumerate(sessions, 1):
        print(f"  {i}. {session['device_info']} from {session['ip_address']} ({session['location']}) - {session['age']}")
    
    # Show security summary
    print("\n🔒 Security Summary:")
    security_summary = auth_service.get_security_summary("admin")
    if 'error' not in security_summary:
        print(f"  Security Score: {security_summary['security_score']['score']}/100 ({security_summary['security_score']['risk_level']} Risk)")
        print(f"  Active Sessions: {security_summary['total_active_sessions']}")
        print(f"  Unique IPs: {security_summary['unique_ip_addresses']}")
        print(f"  Sessions (24h): {security_summary['sessions_last_24h']}")
        
        if security_summary['security_score']['warnings']:
            print("  ⚠️  Security Warnings:")
            for warning in security_summary['security_score']['warnings']:
                print(f"    - {warning}")
    else:
        print(f"  Error: {security_summary['error']}")
    
    print("\n🎯 Ready for session management testing!")
    print("Now run the main app and:")
    print("1. Login as admin/admin123")
    print("2. Go to Users tab") 
    print("3. Click 'Sessions' button for the admin user")
    print("4. Test session termination and management features")

if __name__ == "__main__":
    create_demo_sessions()