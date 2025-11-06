import hashlib
from typing import Optional, Dict
from django.db import transaction
from django.db.models import Sum, Count, Q
from ..models import File


class DeduplicationService:
    """Service for handling file deduplication operations"""
    
    CHUNK_SIZE = 8192  # 8KB chunks for memory-efficient file reading
    
    @staticmethod
    def compute_file_hash(file_obj) -> str:
        """
        Compute SHA-256 hash of file content.
        
        Args:
            file_obj: Django UploadedFile or File object
            
        Returns:
            64-character hexadecimal hash string
        """
        sha256_hash = hashlib.sha256()
        
        # Reset file pointer to beginning
        file_obj.seek(0)
        
        # Read file in chunks for memory efficiency
        while chunk := file_obj.read(DeduplicationService.CHUNK_SIZE):
            sha256_hash.update(chunk)
        
        # Reset file pointer for subsequent operations
        file_obj.seek(0)
        
        return sha256_hash.hexdigest()
    
    @staticmethod
    def find_duplicate(file_hash: str) -> Optional[File]:
        """
        Find existing file with matching hash.
        
        Args:
            file_hash: SHA-256 hash string to search for
            
        Returns:
            File instance if duplicate found, None otherwise
        """
        try:
            # Query for non-duplicate files with matching hash
            # We want the original file, not a duplicate reference
            return File.objects.filter(
                file_hash=file_hash,
                is_duplicate=False
            ).first()
        except File.DoesNotExist:
            return None
    
    @staticmethod
    @transaction.atomic
    def create_duplicate_reference(
        original_file: File,
        filename: str,
        file_type: str,
        size: int
    ) -> File:
        """
        Create a reference to existing file without storing physical file.
        
        Args:
            original_file: The original File instance to reference
            filename: Original filename of the duplicate upload
            file_type: MIME type of the file
            size: File size in bytes
            
        Returns:
            New File instance marked as duplicate
        """
        # Increment reference count on original file
        original_file.reference_count += 1
        original_file.save(update_fields=['reference_count'])
        
        # Create duplicate reference without physical file
        duplicate_file = File.objects.create(
            file=None,  # No physical file stored
            original_filename=filename,
            file_type=file_type,
            size=size,
            file_hash=original_file.file_hash,
            is_duplicate=True,
            original_file=original_file,
            reference_count=0  # Duplicates don't have their own references
        )
        
        return duplicate_file
    
    @staticmethod
    def calculate_storage_savings() -> Dict:
        """
        Calculate total storage saved through deduplication.
        
        Returns:
            Dictionary containing:
                - total_files: Total number of file records
                - unique_files: Number of unique files (non-duplicates)
                - duplicate_references: Number of duplicate references
                - storage_saved_bytes: Total bytes saved
                - storage_saved_readable: Human-readable format
        """
        # Get all file statistics
        total_files = File.objects.count()
        unique_files = File.objects.filter(is_duplicate=False).count()
        duplicate_references = File.objects.filter(is_duplicate=True).count()
        
        # Calculate storage savings
        # For each unique file, savings = size * (reference_count - 1)
        storage_saved_bytes = 0
        
        unique_file_records = File.objects.filter(
            is_duplicate=False,
            reference_count__gt=1
        ).values('size', 'reference_count')
        
        for record in unique_file_records:
            storage_saved_bytes += record['size'] * (record['reference_count'] - 1)
        
        # Convert to human-readable format
        storage_saved_readable = DeduplicationService._format_bytes(storage_saved_bytes)
        
        return {
            'total_files': total_files,
            'unique_files': unique_files,
            'duplicate_references': duplicate_references,
            'storage_saved_bytes': storage_saved_bytes,
            'storage_saved_readable': storage_saved_readable
        }
    
    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """
        Format bytes into human-readable string.
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string (e.g., "1.50 MB")
        """
        if bytes_value == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(bytes_value)
        
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"
