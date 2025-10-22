"""
Encryption and decryption utilities for secure data storage.
"""

import base64
import hashlib
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Union, Optional
import json

class EncryptionManager:
    """Manager for data encryption and decryption operations."""
    
    def __init__(self, password: Optional[str] = None):
        """
        Initialize encryption manager.
        
        Args:
            password: Password for encryption. If None, will use default or generate key.
        """
        self.password = password or self._get_default_password()
        self.key = self._derive_key(self.password)
        self.cipher = Fernet(self.key)
    
    def _get_default_password(self) -> str:
        """Get default password from environment or generate one."""
        # In production, you should use environment variables or secure key management
        default_password = os.environ.get('BMS_ENCRYPTION_PASSWORD')
        if default_password:
            return default_password
        
        # Generate a default password based on system info (not secure for production)
        import platform
        import getpass
        system_info = f"{platform.node()}{getpass.getuser()}{platform.system()}"
        return hashlib.sha256(system_info.encode()).hexdigest()[:32]
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        # Use a fixed salt for consistency (in production, store salt separately)
        salt = b'bms_salt_2024'  # In production, generate and store unique salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_string(self, plaintext: str) -> str:
        """
        Encrypt a string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
    
    def decrypt_string(self, encrypted_text: str) -> str:
        """
        Decrypt a string.
        
        Args:
            encrypted_text: Base64 encoded encrypted string
            
        Returns:
            Decrypted string
        """
        if not encrypted_text:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt string: {str(e)}")
    
    def encrypt_dict(self, data: dict) -> str:
        """
        Encrypt a dictionary by converting to JSON first.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64 encoded encrypted JSON string
        """
        if not data:
            return ""
        
        json_string = json.dumps(data, ensure_ascii=False)
        return self.encrypt_string(json_string)
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """
        Decrypt a dictionary from encrypted JSON.
        
        Args:
            encrypted_data: Base64 encoded encrypted JSON string
            
        Returns:
            Decrypted dictionary
        """
        if not encrypted_data:
            return {}
        
        try:
            json_string = self.decrypt_string(encrypted_data)
            return json.loads(json_string)
        except Exception as e:
            raise ValueError(f"Failed to decrypt dictionary: {str(e)}")
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Encrypt a file.
        
        Args:
            file_path: Path to file to encrypt
            output_path: Path for encrypted file (default: add .enc extension)
            
        Returns:
            Path to encrypted file
        """
        if not output_path:
            output_path = f"{file_path}.enc"
        
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        encrypted_data = self.cipher.encrypt(file_data)
        
        with open(output_path, 'wb') as file:
            file.write(encrypted_data)
        
        return output_path
    
    def decrypt_file(self, encrypted_file_path: str, output_path: Optional[str] = None) -> str:
        """
        Decrypt a file.
        
        Args:
            encrypted_file_path: Path to encrypted file
            output_path: Path for decrypted file (default: remove .enc extension)
            
        Returns:
            Path to decrypted file
        """
        if not output_path:
            if encrypted_file_path.endswith('.enc'):
                output_path = encrypted_file_path[:-4]
            else:
                output_path = f"{encrypted_file_path}.dec"
        
        with open(encrypted_file_path, 'rb') as file:
            encrypted_data = file.read()
        
        decrypted_data = self.cipher.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as file:
            file.write(decrypted_data)
        
        return output_path
    
    def generate_new_key(self) -> bytes:
        """Generate a new encryption key."""
        return Fernet.generate_key()
    
    def change_password(self, new_password: str):
        """Change encryption password."""
        self.password = new_password
        self.key = self._derive_key(self.password)
        self.cipher = Fernet(self.key)
    
    def verify_encryption(self, plaintext: str) -> bool:
        """Verify that encryption/decryption works correctly."""
        try:
            encrypted = self.encrypt_string(plaintext)
            decrypted = self.decrypt_string(encrypted)
            return decrypted == plaintext
        except Exception:
            return False

class DataIntegrityManager:
    """Manager for data integrity verification."""
    
    @staticmethod
    def calculate_hash(data: Union[str, bytes]) -> str:
        """Calculate SHA-256 hash of data."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def verify_hash(data: Union[str, bytes], expected_hash: str) -> bool:
        """Verify data integrity using hash."""
        calculated_hash = DataIntegrityManager.calculate_hash(data)
        return calculated_hash == expected_hash
    
    @staticmethod
    def create_checksum(data: dict) -> str:
        """Create checksum for dictionary data."""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return DataIntegrityManager.calculate_hash(sorted_data)
    
    @staticmethod
    def verify_checksum(data: dict, expected_checksum: str) -> bool:
        """Verify dictionary data integrity."""
        calculated_checksum = DataIntegrityManager.create_checksum(data)
        return calculated_checksum == expected_checksum
