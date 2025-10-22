"""
Backup and restore utilities for BMS data.
"""

import os
import shutil
import json
import gzip
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from .encryption import EncryptionManager
from .compression import CompressionManager, CompressionType
from ..config import SecurityConfig

class BackupManager:
    """Manager for backup and restore operations."""
    
    def __init__(self, backup_dir: str = "backups", 
                 encryption_password: Optional[str] = None,
                 compression_type: CompressionType = CompressionType.GZIP):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backups
            encryption_password: Password for backup encryption
            compression_type: Type of compression to use
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.encryption_manager = EncryptionManager(encryption_password) if encryption_password else None
        self.compression_manager = CompressionManager(compression_type)
        
        # Create subdirectories
        self.encrypted_backups_dir = self.backup_dir / "encrypted"
        self.unencrypted_backups_dir = self.backup_dir / "unencrypted"
        self.encrypted_backups_dir.mkdir(exist_ok=True)
        self.unencrypted_backups_dir.mkdir(exist_ok=True)
    
    def create_backup(self, source_db_path: str, 
                     include_metadata: bool = True,
                     compress: bool = True,
                     encrypt: bool = True) -> str:
        """
        Create a backup of the database.
        
        Args:
            source_db_path: Path to source database
            include_metadata: Include backup metadata
            compress: Whether to compress the backup
            encrypt: Whether to encrypt the backup
            
        Returns:
            Path to created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"bms_backup_{timestamp}"
        
        # Copy database file
        if encrypt and self.encryption_manager:
            backup_path = self.encrypted_backups_dir / f"{base_name}.db"
        else:
            backup_path = self.unencrypted_backups_dir / f"{base_name}.db"
        
        shutil.copy2(source_db_path, backup_path)
        
        # Create metadata file
        if include_metadata:
            metadata = {
                'backup_timestamp': datetime.now().isoformat(),
                'source_file': source_db_path,
                'compressed': compress,
                'encrypted': encrypt,
                'compression_type': self.compression_manager.compression_type.value,
                'file_size': os.path.getsize(backup_path),
                'version': '1.0'
            }
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        # Compress if requested
        if compress:
            compressed_path = self.compression_manager.compress_file(str(backup_path))
            os.remove(backup_path)  # Remove uncompressed file
            backup_path = Path(compressed_path)
        
        # Encrypt if requested
        if encrypt and self.encryption_manager:
            encrypted_path = self.encryption_manager.encrypt_file(str(backup_path))
            os.remove(backup_path)  # Remove unencrypted file
            backup_path = Path(encrypted_path)
        
        return str(backup_path)
    
    def restore_backup(self, backup_path: str, 
                      target_db_path: str,
                      password: Optional[str] = None) -> bool:
        """
        Restore from backup.
        
        Args:
            backup_path: Path to backup file
            target_db_path: Path to restore database to
            password: Password for encrypted backups
            
        Returns:
            True if restore successful, False otherwise
        """
        try:
            backup_path = Path(backup_path)
            temp_path = backup_path.with_suffix('.temp')
            
            # Copy backup to temp location
            shutil.copy2(backup_path, temp_path)
            
            # Decrypt if needed
            if backup_path.suffix == '.enc' or (password and self.encryption_manager):
                if password:
                    temp_encryption_manager = EncryptionManager(password)
                    decrypted_path = temp_encryption_manager.decrypt_file(str(temp_path))
                    os.remove(temp_path)
                    temp_path = Path(decrypted_path)
                elif self.encryption_manager:
                    decrypted_path = self.encryption_manager.decrypt_file(str(temp_path))
                    os.remove(temp_path)
                    temp_path = Path(decrypted_path)
            
            # Decompress if needed
            if temp_path.suffix in ['.gz', '.bz2', '.xz', '.zlib']:
                decompressed_path = self.compression_manager.decompress_file(str(temp_path))
                os.remove(temp_path)
                temp_path = Path(decompressed_path)
            
            # Copy to target location
            shutil.copy2(temp_path, target_db_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            return True
            
        except Exception as e:
            print(f"Restore failed: {str(e)}")
            return False
    
    def list_backups(self, include_encrypted: bool = True, 
                    include_unencrypted: bool = True) -> List[Dict[str, Any]]:
        """
        List available backups.
        
        Args:
            include_encrypted: Include encrypted backups
            include_unencrypted: Include unencrypted backups
            
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        # Scan encrypted backups
        if include_encrypted:
            for backup_file in self.encrypted_backups_dir.glob("*.db*"):
                backup_info = self._get_backup_info(backup_file, encrypted=True)
                if backup_info:
                    backups.append(backup_info)
        
        # Scan unencrypted backups
        if include_unencrypted:
            for backup_file in self.unencrypted_backups_dir.glob("*.db*"):
                backup_info = self._get_backup_info(backup_file, encrypted=False)
                if backup_info:
                    backups.append(backup_info)
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def _get_backup_info(self, backup_file: Path, encrypted: bool) -> Optional[Dict[str, Any]]:
        """Get information about a backup file."""
        try:
            # Check for metadata file
            metadata_file = backup_file.with_suffix('.json')
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            # Get file stats
            stat = backup_file.stat()
            
            return {
                'file_path': str(backup_file),
                'filename': backup_file.name,
                'size': stat.st_size,
                'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'encrypted': encrypted,
                'compressed': backup_file.suffix in ['.gz', '.bz2', '.xz', '.zlib'],
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"Error reading backup info for {backup_file}: {str(e)}")
            return None
    
    def cleanup_old_backups(self, days_to_keep: int = SecurityConfig.BACKUP_RETENTION_DAYS):
        """
        Clean up old backups.
        
        Args:
            days_to_keep: Number of days to keep backups
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        # Clean up encrypted backups
        for backup_file in self.encrypted_backups_dir.glob("*.db*"):
            if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                backup_file.unlink()
                # Also delete metadata file
                metadata_file = backup_file.with_suffix('.json')
                if metadata_file.exists():
                    metadata_file.unlink()
                deleted_count += 1
        
        # Clean up unencrypted backups
        for backup_file in self.unencrypted_backups_dir.glob("*.db*"):
            if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                backup_file.unlink()
                # Also delete metadata file
                metadata_file = backup_file.with_suffix('.json')
                if metadata_file.exists():
                    metadata_file.unlink()
                deleted_count += 1
        
        return deleted_count
    
    def verify_backup(self, backup_path: str, password: Optional[str] = None) -> bool:
        """
        Verify backup integrity.
        
        Args:
            backup_path: Path to backup file
            password: Password for encrypted backups
            
        Returns:
            True if backup is valid, False otherwise
        """
        try:
            backup_path = Path(backup_path)
            temp_path = backup_path.with_suffix('.temp')
            
            # Copy backup to temp location
            shutil.copy2(backup_path, temp_path)
            
            # Decrypt if needed
            if backup_path.suffix == '.enc' or (password and self.encryption_manager):
                if password:
                    temp_encryption_manager = EncryptionManager(password)
                    decrypted_path = temp_encryption_manager.decrypt_file(str(temp_path))
                    os.remove(temp_path)
                    temp_path = Path(decrypted_path)
                elif self.encryption_manager:
                    decrypted_path = self.encryption_manager.decrypt_file(str(temp_path))
                    os.remove(temp_path)
                    temp_path = Path(decrypted_path)
            
            # Decompress if needed
            if temp_path.suffix in ['.gz', '.bz2', '.xz', '.zlib']:
                decompressed_path = self.compression_manager.decompress_file(str(temp_path))
                os.remove(temp_path)
                temp_path = Path(decompressed_path)
            
            # Verify it's a valid SQLite database
            import sqlite3
            conn = sqlite3.connect(str(temp_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            # Clean up temp file
            os.remove(temp_path)
            
            # Check if we have expected tables
            expected_tables = ['handovers', 'requirements', 'issues', 'test_suites']
            table_names = [table[0] for table in tables]
            return all(table in table_names for table in expected_tables)
            
        except Exception as e:
            print(f"Backup verification failed: {str(e)}")
            return False
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics."""
        backups = self.list_backups()
        
        if not backups:
            return {
                'total_backups': 0,
                'total_size': 0,
                'encrypted_count': 0,
                'unencrypted_count': 0,
                'compressed_count': 0,
                'oldest_backup': None,
                'newest_backup': None
            }
        
        total_size = sum(backup['size'] for backup in backups)
        encrypted_count = sum(1 for backup in backups if backup['encrypted'])
        unencrypted_count = len(backups) - encrypted_count
        compressed_count = sum(1 for backup in backups if backup['compressed'])
        
        timestamps = [datetime.fromisoformat(backup['timestamp']) for backup in backups]
        
        return {
            'total_backups': len(backups),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'encrypted_count': encrypted_count,
            'unencrypted_count': unencrypted_count,
            'compressed_count': compressed_count,
            'oldest_backup': min(timestamps).isoformat() if timestamps else None,
            'newest_backup': max(timestamps).isoformat() if timestamps else None
        }
