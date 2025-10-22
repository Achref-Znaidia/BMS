"""
Secure database service with encryption and compression for data storage optimization.
"""

import json
import base64
import os
import time
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import contextmanager

from .database import DatabaseManager
from ..utils.encryption import EncryptionManager, DataIntegrityManager
from ..utils.compression import CompressionManager, CompressionType
from ..config import SecurityConfig


class SecureDatabaseManager:
    """
    Secure database manager that adds encryption and compression to database operations.
    """
    
    def __init__(self, db_name: str = None, encryption_password: str = None):
        """
        Initialize secure database manager.
        
        Args:
            db_name: Database filename
            encryption_password: Password for encryption (optional)
        """
        self.db_manager = DatabaseManager(db_name) if db_name else DatabaseManager()
        
        # Initialize security components
        self.encryption_manager = EncryptionManager(encryption_password)
        self.compression_manager = CompressionManager(
            CompressionType(SecurityConfig.DEFAULT_COMPRESSION_TYPE)
        )
        
        # Security settings from config
        self.enable_encryption = SecurityConfig.ENABLE_ENCRYPTION
        self.enable_compression = SecurityConfig.ENABLE_COMPRESSION
        self.compression_level = SecurityConfig.COMPRESSION_LEVEL
        self.enable_checksums = SecurityConfig.ENABLE_CHECKSUMS
        
        # Create metadata table for security info
        self._create_security_metadata_table()
    
    def _create_security_metadata_table(self):
        """Create table for storing security metadata."""
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_metadata (
                table_name TEXT PRIMARY KEY,
                encryption_enabled BOOLEAN,
                compression_enabled BOOLEAN,
                compression_type TEXT,
                checksum TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _update_security_metadata(self, table_name: str, data: Dict[str, Any]):
        """Update security metadata for a table."""
        if not self.enable_checksums:
            return
            
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()
        
        # Calculate checksum of the data
        checksum = DataIntegrityManager.create_checksum(data) if data else ""
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO security_metadata 
            (table_name, encryption_enabled, compression_enabled, compression_type, checksum, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            table_name,
            self.enable_encryption,
            self.enable_compression,
            self.compression_manager.compression_type.value,
            checksum,
            current_time,
            current_time
        ))
        
        conn.commit()
        conn.close()
    
    def _verify_data_integrity(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Verify data integrity using checksums."""
        if not self.enable_checksums or not data:
            return True
            
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT checksum FROM security_metadata WHERE table_name = ?', (table_name,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return True  # No checksum available, assume valid
            
        stored_checksum = result[0]
        calculated_checksum = DataIntegrityManager.create_checksum(data)
        
        return DataIntegrityManager.verify_checksum(data, stored_checksum)
    
    def _secure_data(self, data: Any) -> str:
        """
        Apply compression and encryption to data.
        
        Args:
            data: Data to secure (dict, list, or string)
            
        Returns:
            Base64 encoded secured data
        """
        if data is None:
            return ""
        
        # Convert to JSON string if not already
        if isinstance(data, (dict, list)):
            json_data = json.dumps(data, ensure_ascii=False)
        else:
            json_data = str(data)
        
        # Apply compression if enabled
        if self.enable_compression:
            compressed_data = self.compression_manager.compress_string(
                json_data, self.compression_level
            )
            # Convert bytes to base64 for storage
            processed_data = base64.b64encode(compressed_data).decode('utf-8')
        else:
            processed_data = json_data
        
        # Apply encryption if enabled
        if self.enable_encryption:
            encrypted_data = self.encryption_manager.encrypt_string(processed_data)
            return encrypted_data
        
        return processed_data
    
    def _unsecure_data(self, secured_data: str) -> Any:
        """
        Decrypt and decompress data with fallback for mixed security states.
        
        Args:
            secured_data: Base64 encoded secured data
            
        Returns:
            Original data
        """
        if not secured_data:
            return None
        
        # Try multiple approaches to handle different security configurations
        attempts = [
            # Current configuration
            (self.enable_encryption, self.enable_compression),
            # Try without encryption
            (False, self.enable_compression),
            # Try without compression
            (self.enable_encryption, False),
            # Try plain text
            (False, False)
        ]
        
        for try_encryption, try_compression in attempts:
            try:
                processed_data = secured_data
                
                # Decrypt if needed
                if try_encryption:
                    try:
                        processed_data = self.encryption_manager.decrypt_string(processed_data)
                    except Exception:
                        continue  # Try next combination
                
                # Decompress if needed
                if try_compression:
                    try:
                        # Convert base64 back to bytes
                        compressed_bytes = base64.b64decode(processed_data.encode('utf-8'))
                        json_data = self.compression_manager.decompress_string(compressed_bytes)
                    except Exception:
                        continue  # Try next combination
                else:
                    json_data = processed_data
                
                # Parse JSON back to original structure
                try:
                    return json.loads(json_data)
                except json.JSONDecodeError:
                    # Return as string if it's not JSON
                    return json_data
                    
            except Exception:
                continue  # Try next combination
        
        # If all attempts failed, try to return as plain text
        try:
            return json.loads(secured_data)
        except:
            return secured_data
    
    @contextmanager
    def _get_connection_with_retry(self, max_retries=5, retry_delay=0.1):
        """Get database connection with retry logic and proper resource management."""
        conn = None
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_manager.db_name, timeout=30.0)
                conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode for better concurrency
                conn.execute('PRAGMA busy_timeout=30000')  # 30 second timeout
                yield conn
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    if conn:
                        try:
                            conn.close()
                        except:
                            pass
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise
            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                raise
            finally:
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
    
    def save_app_data(self, app_data: Dict[str, Any]) -> bool:
        """
        Save application data securely to a special table.
        
        Args:
            app_data: Application data dictionary
            
        Returns:
            Success status
        """
        try:
            with self._get_connection_with_retry() as conn:
                cursor = conn.cursor()
                
                # Create app_data table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_data (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                
                current_time = datetime.now().isoformat()
                
                # Save each section of app_data in a single transaction
                for key, value in app_data.items():
                    if key == "theme_mode":
                        # Save theme_mode as string, not as object
                        secured_value = self._secure_data(value.value if hasattr(value, 'value') else str(value))
                    else:
                        secured_value = self._secure_data(value)
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO app_data (key, value, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                    ''', (key, secured_value, current_time, current_time))
            
            # Update security metadata after successful save
            try:
                for key, value in app_data.items():
                    if isinstance(value, (dict, list)):
                        self._update_security_metadata(f"app_data_{key}", 
                                                     value if isinstance(value, dict) else {"data": value})
            except Exception as meta_error:
                print(f"Error updating metadata (non-critical): {meta_error}")
            
            return True
            
        except Exception as e:
            print(f"Error saving app data: {e}")
            return False
    
    def load_app_data(self) -> Dict[str, Any]:
        """
        Load application data from secure storage.
        
        Returns:
            Application data dictionary
        """
        try:
            with self._get_connection_with_retry() as conn:
                cursor = conn.cursor()
                
                # Check if app_data table exists
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='app_data'
                ''')
                
                if not cursor.fetchone():
                    return {}  # Table doesn't exist, return empty data
                
                cursor.execute('SELECT key, value FROM app_data')
                rows = cursor.fetchall()
            
            app_data = {}
            for key, secured_value in rows:
                try:
                    unsecured_value = self._unsecure_data(secured_value)
                    app_data[key] = unsecured_value
                except Exception as e:
                    print(f"Error loading data for key '{key}': {e}")
                    # Skip corrupted data entries
                    continue
            
            return app_data
            
        except Exception as e:
            print(f"Error loading app data: {e}")
            return {}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about storage usage and compression benefits.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            # Get database file size
            db_size = os.path.getsize(self.db_manager.db_name) if os.path.exists(self.db_manager.db_name) else 0
            
            with self._get_connection_with_retry() as conn:
                cursor = conn.cursor()
                
                # Get table sizes
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ''')
                tables = cursor.fetchall()
                
                table_stats = {}
                total_records = 0
                
                for (table_name,) in tables:
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                        record_count = cursor.fetchone()[0]
                        total_records += record_count
                        
                        # Calculate approximate data size (rough estimate)
                        cursor.execute(f'SELECT * FROM {table_name} LIMIT 1')
                        sample_row = cursor.fetchone()
                        if sample_row:
                            estimated_row_size = sum(len(str(col)) for col in sample_row)
                            estimated_table_size = estimated_row_size * record_count
                        else:
                            estimated_table_size = 0
                        
                        table_stats[table_name] = {
                            'records': record_count,
                            'estimated_size_bytes': estimated_table_size
                        }
                    except Exception as table_error:
                        print(f"Error getting stats for table {table_name}: {table_error}")
                        table_stats[table_name] = {'records': 0, 'estimated_size_bytes': 0}
            
            return {
                'database_file_size_bytes': db_size,
                'database_file_size_mb': round(db_size / (1024 * 1024), 2),
                'total_records': total_records,
                'table_statistics': table_stats,
                'security_features': {
                    'encryption_enabled': self.enable_encryption,
                    'compression_enabled': self.enable_compression,
                    'compression_type': self.compression_manager.compression_type.value,
                    'compression_level': self.compression_level,
                    'checksums_enabled': self.enable_checksums
                }
            }
            
        except Exception as e:
            print(f"Error getting storage stats: {e}")
            return {}
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        Create an encrypted and compressed backup of the entire database.
        
        Args:
            backup_path: Path for backup file (optional)
            
        Returns:
            Path to backup file
        """
        if not backup_path:
            # Use existing backups folder
            import os
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}.bms")
        
        try:
            # Load all app data
            app_data = self.load_app_data()
            
            # Create backup data structure
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'app_data': app_data,
                'security_metadata': self.get_storage_stats()
            }
            
            # Compress and encrypt the backup
            if SecurityConfig.BACKUP_COMPRESSION:
                compressed_data = self.compression_manager.compress_dict(
                    backup_data, self.compression_level
                )
                backup_content = base64.b64encode(compressed_data).decode('utf-8')
            else:
                backup_content = json.dumps(backup_data, ensure_ascii=False)
            
            if SecurityConfig.BACKUP_ENCRYPTION:
                backup_content = self.encryption_manager.encrypt_string(backup_content)
            
            # Write backup file
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
            
            return backup_path
            
        except Exception as e:
            raise ValueError(f"Backup failed: {str(e)}")
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from encrypted and compressed backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Success status
        """
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Read backup file
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            
            # Decrypt if needed
            if SecurityConfig.BACKUP_ENCRYPTION:
                backup_content = self.encryption_manager.decrypt_string(backup_content)
            
            # Decompress if needed
            if SecurityConfig.BACKUP_COMPRESSION:
                compressed_bytes = base64.b64decode(backup_content.encode('utf-8'))
                json_content = self.compression_manager.decompress_string(compressed_bytes)
                backup_data = json.loads(json_content)
            else:
                backup_data = json.loads(backup_content)
            
            # Validate backup structure
            if 'app_data' not in backup_data:
                raise ValueError("Invalid backup file format")
            
            # Restore app data
            success = self.save_app_data(backup_data['app_data'])
            
            return success
            
        except Exception as e:
            print(f"Restore failed: {str(e)}")
            return False
    
    def update_security_settings(self, encryption: bool = None, compression: bool = None, checksums: bool = None) -> bool:
        """
        Update security settings and re-save data with new configuration.
        
        Args:
            encryption: Enable/disable encryption
            compression: Enable/disable compression
            checksums: Enable/disable checksums
            
        Returns:
            Success status
        """
        try:
            # Load current data with old settings
            current_data = self.load_app_data()
            
            # Update settings
            if encryption is not None:
                self.enable_encryption = encryption
            if compression is not None:
                self.enable_compression = compression
            if checksums is not None:
                self.enable_checksums = checksums
            
            # If we have data, re-save it with new security settings
            if current_data:
                success = self.save_app_data(current_data)
                return success
            
            return True
            
        except Exception as e:
            print(f"Error updating security settings: {e}")
            return False
    
    def get_current_security_config(self) -> Dict[str, bool]:
        """Get current security configuration."""
        return {
            'encryption_enabled': self.enable_encryption,
            'compression_enabled': self.enable_compression,
            'checksums_enabled': self.enable_checksums,
            'compression_type': self.compression_manager.compression_type.value
        }
    
    def clear_all_data(self) -> bool:
        """
        Clear all application data from the database.
        WARNING: This will permanently delete all data!
        
        Returns:
            Success status
        """
        try:
            # Clear all app data tables by saving empty data
            empty_data = {
                "handovers": [],
                "requirements": [],
                "issues": [],
                "test_suites": [],
                "recent_activities": [],
                "theme_mode": "light"
            }
            
            # Save empty data structure
            success = self.save_app_data(empty_data)
            
            if success:
                print("Database cleared successfully")
            
            return success
            
        except Exception as e:
            print(f"Error clearing database: {e}")
            return False
    
    # Delegate other database operations to the underlying DatabaseManager
    def __getattr__(self, name):
        """Delegate unknown method calls to the underlying DatabaseManager."""
        return getattr(self.db_manager, name)
