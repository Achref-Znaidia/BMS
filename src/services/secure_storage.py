"""
Secure data storage service with encryption and compression.
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import base64

from ..utils.encryption import EncryptionManager, DataIntegrityManager
from ..utils.compression import CompressionManager, CompressionType
from ..config import DatabaseConfig

class SecureStorageManager:
    """Secure storage manager with encryption and compression."""
    
    def __init__(self, db_name: str = DatabaseConfig.DB_NAME, 
                 password: Optional[str] = None,
                 compression_type: CompressionType = CompressionType.GZIP,
                 enable_compression: bool = True,
                 enable_encryption: bool = True):
        """
        Initialize secure storage manager.
        
        Args:
            db_name: Database file name
            password: Encryption password
            compression_type: Type of compression to use
            enable_compression: Whether to enable compression
            enable_encryption: Whether to enable encryption
        """
        self.db_name = db_name
        self.enable_compression = enable_compression
        self.enable_encryption = enable_encryption
        
        # Initialize encryption and compression managers
        if self.enable_encryption:
            self.encryption_manager = EncryptionManager(password)
        else:
            self.encryption_manager = None
            
        if self.enable_compression:
            self.compression_manager = CompressionManager(compression_type)
        else:
            self.compression_manager = None
        
        self._create_secure_tables()
        self._insert_sample_data()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_name)
    
    def _create_secure_tables(self):
        """Create secure database tables with metadata."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Handovers table with encryption metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS handovers (
                id TEXT PRIMARY KEY,
                encrypted_data BLOB,
                compression_type TEXT,
                encryption_checksum TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Requirements table with encryption metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                encrypted_data BLOB,
                compression_type TEXT,
                encryption_checksum TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Issues table with encryption metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                id TEXT PRIMARY KEY,
                encrypted_data BLOB,
                compression_type TEXT,
                encryption_checksum TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Test suites table with encryption metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_suites (
                id TEXT PRIMARY KEY,
                encrypted_data BLOB,
                compression_type TEXT,
                encryption_checksum TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Security settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_settings (
                id INTEGER PRIMARY KEY,
                encryption_enabled BOOLEAN,
                compression_enabled BOOLEAN,
                compression_type TEXT,
                last_password_change TEXT,
                created_at TEXT
            )
        ''')
        
        # Store security settings
        current_time = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO security_settings 
            (id, encryption_enabled, compression_enabled, compression_type, last_password_change, created_at)
            VALUES (1, ?, ?, ?, ?, ?)
        ''', (
            self.enable_encryption,
            self.enable_compression,
            self.compression_manager.compression_type.value if self.compression_manager else 'none',
            current_time,
            current_time
        ))
        
        conn.commit()
        conn.close()
    
    def _encrypt_and_compress_data(self, data: Dict[str, Any]) -> tuple:
        """
        Encrypt and compress data.
        
        Args:
            data: Data dictionary to process
            
        Returns:
            Tuple of (processed_data, compression_type, checksum)
        """
        # Convert to JSON string
        json_data = json.dumps(data, ensure_ascii=False)
        
        # Compress if enabled
        if self.enable_compression and self.compression_manager:
            compressed_data = self.compression_manager.compress_string(json_data)
            compression_type = self.compression_manager.compression_type.value
        else:
            compressed_data = json_data.encode('utf-8')
            compression_type = 'none'
        
        # Encrypt if enabled
        if self.enable_encryption and self.encryption_manager:
            encrypted_data = self.encryption_manager.cipher.encrypt(compressed_data)
        else:
            encrypted_data = compressed_data
        
        # Calculate checksum for integrity verification
        checksum = DataIntegrityManager.calculate_hash(encrypted_data)
        
        return encrypted_data, compression_type, checksum
    
    def _decrypt_and_decompress_data(self, encrypted_data: bytes, compression_type: str, 
                                   checksum: str) -> Dict[str, Any]:
        """
        Decrypt and decompress data.
        
        Args:
            encrypted_data: Encrypted data bytes
            compression_type: Type of compression used
            checksum: Expected checksum for verification
            
        Returns:
            Decrypted and decompressed data dictionary
        """
        # Verify data integrity
        if not DataIntegrityManager.verify_hash(encrypted_data, checksum):
            raise ValueError("Data integrity check failed - data may be corrupted")
        
        # Decrypt if enabled
        if self.enable_encryption and self.encryption_manager:
            decrypted_data = self.encryption_manager.cipher.decrypt(encrypted_data)
        else:
            decrypted_data = encrypted_data
        
        # Decompress if enabled
        if compression_type != 'none' and self.compression_manager:
            decompressed_data = self.compression_manager.decompress_bytes(decrypted_data)
        else:
            decompressed_data = decrypted_data
        
        # Convert back to dictionary
        json_string = decompressed_data.decode('utf-8')
        return json.loads(json_string)
    
    def _insert_sample_data(self):
        """Insert sample data if tables are empty."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if we already have data
        cursor.execute("SELECT COUNT(*) FROM handovers")
        if cursor.fetchone()[0] == 0:
            current_time = datetime.now().isoformat()
            
            # Sample handover data
            sample_handover = {
                'from_team': 'Coverage',
                'to_team': 'Analysis',
                'date': '2024-01-15',
                'description': 'Handover of regression test results',
                'documents': ['test_report_001.pdf', 'coverage_metrics.xlsx'],
                'status': 'Completed'
            }
            
            encrypted_data, compression_type, checksum = self._encrypt_and_compress_data(sample_handover)
            
            cursor.execute('''
                INSERT INTO handovers (id, encrypted_data, compression_type, encryption_checksum, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('1', encrypted_data, compression_type, checksum, current_time, current_time))
            
            conn.commit()
        
        conn.close()
    
    # Handover operations
    def add_handover(self, handover_data: Dict[str, Any]) -> str:
        """Add a new handover with encryption and compression."""
        handover_id = handover_data.get('id', f"handover_{datetime.now().timestamp()}")
        current_time = datetime.now().isoformat()
        
        encrypted_data, compression_type, checksum = self._encrypt_and_compress_data(handover_data)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO handovers (id, encrypted_data, compression_type, encryption_checksum, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (handover_id, encrypted_data, compression_type, checksum, current_time, current_time))
        
        conn.commit()
        conn.close()
        return handover_id
    
    def get_handovers(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get handovers with optional filtering."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, encrypted_data, compression_type, encryption_checksum FROM handovers')
        rows = cursor.fetchall()
        conn.close()
        
        handovers = []
        for row in rows:
            try:
                handover_data = self._decrypt_and_decompress_data(row[1], row[2], row[3])
                handover_data['id'] = row[0]
                
                # Apply status filter if specified
                if not status_filter or status_filter == "All" or handover_data.get('status') == status_filter:
                    handovers.append(handover_data)
            except Exception as e:
                print(f"Error decrypting handover {row[0]}: {str(e)}")
                continue
        
        return handovers
    
    def update_handover(self, handover_id: str, handover_data: Dict[str, Any]):
        """Update an existing handover."""
        current_time = datetime.now().isoformat()
        
        encrypted_data, compression_type, checksum = self._encrypt_and_compress_data(handover_data)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE handovers 
            SET encrypted_data = ?, compression_type = ?, encryption_checksum = ?, updated_at = ?
            WHERE id = ?
        ''', (encrypted_data, compression_type, checksum, current_time, handover_id))
        
        conn.commit()
        conn.close()
    
    def delete_handover(self, handover_id: str) -> bool:
        """Delete a handover."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM handovers WHERE id = ?', (handover_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    # Similar methods for other entities (requirements, issues, test_suites)
    # For brevity, I'll implement the pattern for requirements
    
    def add_requirement(self, requirement_data: Dict[str, Any]) -> str:
        """Add a new requirement with encryption and compression."""
        requirement_id = requirement_data.get('id', f"req_{datetime.now().timestamp()}")
        current_time = datetime.now().isoformat()
        
        encrypted_data, compression_type, checksum = self._encrypt_and_compress_data(requirement_data)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO requirements (id, encrypted_data, compression_type, encryption_checksum, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (requirement_id, encrypted_data, compression_type, checksum, current_time, current_time))
        
        conn.commit()
        conn.close()
        return requirement_id
    
    def get_requirements(self, status_filter: Optional[str] = None, 
                        priority_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get requirements with optional filtering."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, encrypted_data, compression_type, encryption_checksum FROM requirements')
        rows = cursor.fetchall()
        conn.close()
        
        requirements = []
        for row in rows:
            try:
                requirement_data = self._decrypt_and_decompress_data(row[1], row[2], row[3])
                requirement_data['id'] = row[0]
                
                # Apply filters
                if status_filter and status_filter != "All" and requirement_data.get('status') != status_filter:
                    continue
                if priority_filter and priority_filter != "All" and requirement_data.get('priority') != priority_filter:
                    continue
                
                requirements.append(requirement_data)
            except Exception as e:
                print(f"Error decrypting requirement {row[0]}: {str(e)}")
                continue
        
        return requirements
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security settings."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM security_settings WHERE id = 1')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'encryption_enabled': bool(row[1]),
                'compression_enabled': bool(row[2]),
                'compression_type': row[3],
                'last_password_change': row[4],
                'created_at': row[5]
            }
        return {}
    
    def change_password(self, new_password: str):
        """Change encryption password."""
        if self.encryption_manager:
            self.encryption_manager.change_password(new_password)
            
            # Update security settings
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE security_settings 
                SET last_password_change = ?
                WHERE id = 1
            ''', (datetime.now().isoformat(),))
            
            conn.commit()
            conn.close()
    
    def create_backup(self, backup_path: str) -> str:
        """Create encrypted backup of the database."""
        # Copy database file
        import shutil
        shutil.copy2(self.db_name, backup_path)
        
        # Encrypt the backup if encryption is enabled
        if self.enable_encryption and self.encryption_manager:
            encrypted_backup = self.encryption_manager.encrypt_file(backup_path)
            os.remove(backup_path)  # Remove unencrypted backup
            return encrypted_backup
        
        return backup_path
    
    def restore_backup(self, backup_path: str, password: Optional[str] = None) -> bool:
        """Restore from encrypted backup."""
        try:
            # Decrypt backup if it's encrypted
            if password and self.encryption_manager:
                temp_manager = EncryptionManager(password)
                decrypted_backup = temp_manager.decrypt_file(backup_path)
                shutil.copy2(decrypted_backup, self.db_name)
                os.remove(decrypted_backup)  # Clean up temp file
            else:
                shutil.copy2(backup_path, self.db_name)
            
            return True
        except Exception as e:
            print(f"Restore failed: {str(e)}")
            return False
