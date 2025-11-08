"""
File deduplication service with hash-based duplicate detection.
"""
import hashlib
import logging
from typing import Optional, Dict

from django.db import transaction, IntegrityError, DatabaseError

from ..models import File

logger = logging.getLogger('files.deduplication')


# Custom Exceptions
class DeduplicationError(Exception):
    """Base exception for deduplication-related errors."""
    pass


class FileHashError(DeduplicationError):
    """Exception raised when file hash computation fails."""
    pass


class DuplicateDetectionError(DeduplicationError):
    """Exception raised when duplicate detection fails."""
    pass


class ReferenceCreationError(DeduplicationError):
    """Exception raised when creating duplicate reference fails."""
    pass


class DeduplicationService:
    """
    Service for handling file deduplication operations.
    
    Provides methods for computing file hashes, detecting duplicates,
    and managing file references to avoid storing duplicate content.
    """
    
    CHUNK_SIZE = 8192  # 8KB chunks for file reading
    HASH_ALGORITHM = 'sha256'
    
    @classmethod
    def compute_file_hash(cls, file_obj) -> str:
        """
        Compute SHA-256 hash of file content using chunked reading.
        
        Args:
            file_obj: Django UploadedFile or File object
            
        Returns:
            64-character hexadecimal hash string
            
        Raises:
            FileHashError: If file reading or hash computation fails
        """
        try:
            hasher = hashlib.new(cls.HASH_ALGORITHM)
            file_obj.seek(0)
            
            # Read file in chunks to handle large files efficiently
            while chunk := file_obj.read(cls.CHUNK_SIZE):
                hasher.update(chunk)
            
            file_obj.seek(0)  # Reset file pointer
            hash_value = hasher.hexdigest()
            
            logger.debug(f"Computed {cls.HASH_ALGORITHM} hash: {hash_value[:16]}...")
            return hash_value
            
        except (IOError, OSError) as e:
            logger.error(f"File I/O error during hash computation: {e}", exc_info=True)
            raise FileHashError(f"Failed to read file: {e}") from e
        except AttributeError as e:
            logger.error(f"Invalid file object: {e}", exc_info=True)
            raise FileHashError(f"Invalid file object provided: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during hash computation: {e}", exc_info=True)
            raise FileHashError(f"Hash computation failed: {e}") from e
    
    @staticmethod
    def find_duplicate(file_hash: str) -> Optional[File]:
        """
        Find existing original file with matching hash.
        
        Args:
            file_hash: SHA-256 hash string to search for
            
        Returns:
            File instance if duplicate found, None otherwise
            
        Raises:
            DuplicateDetectionError: If database query fails or hash is invalid
        """
        # Validate hash
        if not file_hash or not isinstance(file_hash, str):
            raise DuplicateDetectionError(f"Invalid file hash: {file_hash}")
        
        if len(file_hash) != 64:
            logger.warning(f"Invalid hash length: {len(file_hash)} (expected 64)")
            return None
        
        try:
            # Query for original file with matching hash
            duplicate = File.objects.filter(
                file_hash=file_hash,
                is_duplicate=False
            ).first()
            
            if duplicate:
                logger.info(f"Duplicate found: hash={file_hash[:16]}..., id={duplicate.id}")
            else:
                logger.debug(f"No duplicate found for hash {file_hash[:16]}...")
            
            return duplicate
            
        except DatabaseError as e:
            logger.error(f"Database error during duplicate detection: {e}", exc_info=True)
            raise DuplicateDetectionError(f"Database query failed: {e}") from e
    
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
            
        Raises:
            ReferenceCreationError: If validation fails or database operation fails
        """
        # Validate inputs
        if not original_file:
            raise ReferenceCreationError("Original file cannot be None")
        
        if original_file.is_duplicate:
            raise ReferenceCreationError(
                f"Cannot reference a duplicate file (ID: {original_file.id})"
            )
        
        if not filename or not isinstance(filename, str):
            raise ReferenceCreationError(f"Invalid filename: {filename}")
        
        if size < 0:
            raise ReferenceCreationError(f"Invalid file size: {size}")
        
        try:
            logger.info(
                f"Creating duplicate reference: filename='{filename}', "
                f"original_id={original_file.id}"
            )
            
            # Increment reference count on original
            original_file.reference_count += 1
            original_file.save(update_fields=['reference_count'])
            
            # Create duplicate reference
            duplicate_file = File.objects.create(
                file=None,  # No physical file storage
                original_filename=filename,
                file_type=file_type,
                size=size,
                file_hash=original_file.file_hash,
                is_duplicate=True,
                original_file=original_file,
                reference_count=0
            )
            
            logger.info(
                f"Created duplicate reference: id={duplicate_file.id}, "
                f"original_refs={original_file.reference_count}"
            )
            
            return duplicate_file
            
        except (IntegrityError, DatabaseError) as e:
            logger.error(f"Database error creating duplicate reference: {e}", exc_info=True)
            raise ReferenceCreationError(f"Database operation failed: {e}") from e
    
    @classmethod
    def calculate_storage_savings(cls) -> Dict[str, any]:
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
        # Get counts
        total_files = File.objects.count()
        unique_files = File.objects.filter(is_duplicate=False).count()
        duplicate_references = File.objects.filter(is_duplicate=True).count()
        
        # Calculate storage saved from deduplicated files
        storage_saved_bytes = sum(
            record['size'] * (record['reference_count'] - 1)
            for record in File.objects.filter(
                is_duplicate=False,
                reference_count__gt=1
            ).values('size', 'reference_count')
        )
        
        return {
            'total_files': total_files,
            'unique_files': unique_files,
            'duplicate_references': duplicate_references,
            'storage_saved_bytes': storage_saved_bytes,
            'storage_saved_readable': cls._format_bytes(storage_saved_bytes)
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
        
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        unit_index = 0
        size = float(bytes_value)
        
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"
