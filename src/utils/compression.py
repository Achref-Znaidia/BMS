"""
Compression and decompression utilities for data optimization.
"""

import gzip
import bz2
import lzma
import zlib
import json
from typing import Union, Optional, Dict, Any
from enum import Enum

class CompressionType(Enum):
    """Available compression types."""
    GZIP = "gzip"
    BZIP2 = "bzip2"
    LZMA = "lzma"
    ZLIB = "zlib"
    NONE = "none"

class CompressionManager:
    """Manager for data compression and decompression operations."""
    
    def __init__(self, compression_type: CompressionType = CompressionType.GZIP):
        """
        Initialize compression manager.
        
        Args:
            compression_type: Type of compression to use
        """
        self.compression_type = compression_type
    
    def compress_string(self, data: str, compression_level: int = 6) -> bytes:
        """
        Compress a string.
        
        Args:
            data: String to compress
            compression_level: Compression level (1-9, higher = better compression)
            
        Returns:
            Compressed bytes
        """
        if not data:
            return b""
        
        data_bytes = data.encode('utf-8')
        return self.compress_bytes(data_bytes, compression_level)
    
    def compress_bytes(self, data: bytes, compression_level: int = 6) -> bytes:
        """
        Compress bytes.
        
        Args:
            data: Bytes to compress
            compression_level: Compression level (1-9, higher = better compression)
            
        Returns:
            Compressed bytes
        """
        if not data:
            return b""
        
        if self.compression_type == CompressionType.NONE:
            return data
        
        # Clamp compression level to valid range
        compression_level = max(1, min(9, compression_level))
        
        try:
            if self.compression_type == CompressionType.GZIP:
                return gzip.compress(data, compresslevel=compression_level)
            elif self.compression_type == CompressionType.BZIP2:
                return bz2.compress(data, compresslevel=compression_level)
            elif self.compression_type == CompressionType.LZMA:
                return lzma.compress(data, preset=compression_level)
            elif self.compression_type == CompressionType.ZLIB:
                return zlib.compress(data, level=compression_level)
            else:
                raise ValueError(f"Unsupported compression type: {self.compression_type}")
        except Exception as e:
            raise ValueError(f"Compression failed: {str(e)}")
    
    def decompress_string(self, compressed_data: bytes) -> str:
        """
        Decompress bytes to string.
        
        Args:
            compressed_data: Compressed bytes
            
        Returns:
            Decompressed string
        """
        if not compressed_data:
            return ""
        
        decompressed_bytes = self.decompress_bytes(compressed_data)
        return decompressed_bytes.decode('utf-8')
    
    def decompress_bytes(self, compressed_data: bytes) -> bytes:
        """
        Decompress bytes.
        
        Args:
            compressed_data: Compressed bytes
            
        Returns:
            Decompressed bytes
        """
        if not compressed_data:
            return b""
        
        if self.compression_type == CompressionType.NONE:
            return compressed_data
        
        try:
            if self.compression_type == CompressionType.GZIP:
                return gzip.decompress(compressed_data)
            elif self.compression_type == CompressionType.BZIP2:
                return bz2.decompress(compressed_data)
            elif self.compression_type == CompressionType.LZMA:
                return lzma.decompress(compressed_data)
            elif self.compression_type == CompressionType.ZLIB:
                return zlib.decompress(compressed_data)
            else:
                raise ValueError(f"Unsupported compression type: {self.compression_type}")
        except Exception as e:
            raise ValueError(f"Decompression failed: {str(e)}")
    
    def compress_dict(self, data: dict, compression_level: int = 6) -> bytes:
        """
        Compress a dictionary by converting to JSON first.
        
        Args:
            data: Dictionary to compress
            compression_level: Compression level (1-9)
            
        Returns:
            Compressed bytes
        """
        if not data:
            return b""
        
        json_string = json.dumps(data, ensure_ascii=False)
        return self.compress_string(json_string, compression_level)
    
    def decompress_dict(self, compressed_data: bytes) -> dict:
        """
        Decompress bytes to dictionary.
        
        Args:
            compressed_data: Compressed bytes
            
        Returns:
            Decompressed dictionary
        """
        if not compressed_data:
            return {}
        
        json_string = self.decompress_string(compressed_data)
        return json.loads(json_string)
    
    def compress_file(self, file_path: str, output_path: Optional[str] = None, 
                     compression_level: int = 6) -> str:
        """
        Compress a file.
        
        Args:
            file_path: Path to file to compress
            output_path: Path for compressed file (default: add compression extension)
            compression_level: Compression level (1-9)
            
        Returns:
            Path to compressed file
        """
        if not output_path:
            extension = self._get_compression_extension()
            output_path = f"{file_path}{extension}"
        
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        compressed_data = self.compress_bytes(file_data, compression_level)
        
        with open(output_path, 'wb') as file:
            file.write(compressed_data)
        
        return output_path
    
    def decompress_file(self, compressed_file_path: str, output_path: Optional[str] = None) -> str:
        """
        Decompress a file.
        
        Args:
            compressed_file_path: Path to compressed file
            output_path: Path for decompressed file (default: remove compression extension)
            
        Returns:
            Path to decompressed file
        """
        if not output_path:
            output_path = self._remove_compression_extension(compressed_file_path)
        
        with open(compressed_file_path, 'rb') as file:
            compressed_data = file.read()
        
        decompressed_data = self.decompress_bytes(compressed_data)
        
        with open(output_path, 'wb') as file:
            file.write(decompressed_data)
        
        return output_path
    
    def _get_compression_extension(self) -> str:
        """Get file extension for compression type."""
        extensions = {
            CompressionType.GZIP: '.gz',
            CompressionType.BZIP2: '.bz2',
            CompressionType.LZMA: '.xz',
            CompressionType.ZLIB: '.zlib',
            CompressionType.NONE: ''
        }
        return extensions.get(self.compression_type, '.gz')
    
    def _remove_compression_extension(self, file_path: str) -> str:
        """Remove compression extension from file path."""
        extensions = ['.gz', '.bz2', '.xz', '.zlib']
        for ext in extensions:
            if file_path.endswith(ext):
                return file_path[:-len(ext)]
        return file_path
    
    def get_compression_ratio(self, original_data: bytes, compressed_data: bytes) -> float:
        """
        Calculate compression ratio.
        
        Args:
            original_data: Original data size
            compressed_data: Compressed data size
            
        Returns:
            Compression ratio (0.0 to 1.0, lower is better)
        """
        if not original_data:
            return 0.0
        return len(compressed_data) / len(original_data)
    
    def estimate_compression_benefit(self, data: Union[str, bytes, dict]) -> Dict[str, Any]:
        """
        Estimate compression benefits without actually compressing.
        
        Args:
            data: Data to analyze
            
        Returns:
            Dictionary with compression estimates
        """
        if isinstance(data, dict):
            data = json.dumps(data, ensure_ascii=False)
        elif isinstance(data, str):
            data = data.encode('utf-8')
        
        original_size = len(data)
        
        # Test different compression types
        results = {}
        for comp_type in [CompressionType.GZIP, CompressionType.BZIP2, CompressionType.LZMA, CompressionType.ZLIB]:
            try:
                temp_manager = CompressionManager(comp_type)
                compressed = temp_manager.compress_bytes(data)
                ratio = self.get_compression_ratio(data, compressed)
                results[comp_type.value] = {
                    'compressed_size': len(compressed),
                    'compression_ratio': ratio,
                    'space_saved': original_size - len(compressed),
                    'space_saved_percent': (1 - ratio) * 100
                }
            except Exception:
                results[comp_type.value] = {'error': 'Compression failed'}
        
        return {
            'original_size': original_size,
            'compression_types': results
        }
