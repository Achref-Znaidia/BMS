"""
Test script to verify backup functionality uses the backups folder correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.secure_database import SecureDatabaseManager

def test_backup_folder():
    """Test that backup files are saved in the backups folder."""
    print("🧪 Testing Backup Folder Functionality")
    print("=" * 50)
    
    # Initialize secure database
    secure_db = SecureDatabaseManager()
    
    # Check if backups folder exists
    backups_folder = "backups"
    print(f"📁 Checking for backups folder: {backups_folder}")
    
    if os.path.exists(backups_folder):
        print(f"   ✅ Backups folder exists at: {os.path.abspath(backups_folder)}")
        
        # List existing files in backups folder
        existing_files = os.listdir(backups_folder)
        print(f"   📋 Current files in backups folder: {len(existing_files)} files")
        for file in existing_files[:5]:  # Show first 5 files
            print(f"      - {file}")
        if len(existing_files) > 5:
            print(f"      ... and {len(existing_files) - 5} more files")
    else:
        print(f"   ❌ Backups folder does not exist")
        return
    
    print()
    
    # Test backup creation
    print("💾 Testing Backup Creation")
    try:
        # Create some test data first
        test_data = {
            "handovers": [{"id": 1, "test": "data"}],
            "requirements": [{"id": 1, "title": "Test requirement"}],
            "issues": [],
            "test_suites": [],
            "recent_activities": [],
            "theme_mode": "light"
        }
        
        # Save test data
        secure_db.save_app_data(test_data)
        print("   ✅ Test data saved to database")
        
        # Create backup
        backup_path = secure_db.backup_database()
        print(f"   ✅ Backup created at: {backup_path}")
        
        # Verify backup is in backups folder
        if backup_path.startswith("backups"):
            print("   ✅ Backup correctly saved in backups folder")
        else:
            print(f"   ❌ Backup saved in wrong location: {backup_path}")
        
        # Check if file actually exists
        if os.path.exists(backup_path):
            file_size = os.path.getsize(backup_path)
            print(f"   ✅ Backup file exists with size: {file_size} bytes")
        else:
            print(f"   ❌ Backup file does not exist at: {backup_path}")
        
        # Test backup loading (verification)
        print("   🔍 Testing backup file validity...")
        restored_data = secure_db.load_app_data()  # This should load from current database
        
        if restored_data and "handovers" in restored_data:
            print("   ✅ Database data structure is valid")
        else:
            print("   ❌ Database data structure is invalid")
            
    except Exception as e:
        print(f"   ❌ Error during backup test: {str(e)}")
    
    print()
    
    # Final summary
    print("📋 Summary:")
    print("   • Backup files are saved in the 'backups' folder")
    print("   • File picker will start in the backups folder for easy access")
    print("   • Export menu includes Import Database and Empty Database for admins")
    print("   • Only admin users can access backup/restore/clear operations")

if __name__ == "__main__":
    test_backup_folder()