import hashlib
import logging
from typing import Optional, Dict
from django.db import transaction, IntegrityError, DatabaseError
from django.db.models import Sum, Count, Q
from ..models import File

logger = logging.getLogger('files.deduplication')


class DeduplicationError(Exception):
    """Base exception for deduplication-related errors"""
    pass


class FileHashError(DeduplicationError):
    """Exception raised when file hash computation fails"""
    pass


class DuplicateDetectionError(DeduplicationError):
    """Exception raised when duplicate detection fails"""
    pass


class ReferenceCreationError(DeduplicationError):
    """Exception raised when creating duplicate reference fails"""
    pass


class DeduplicationService:
    """Service for handling file deduplication operations"""
    
    CHUNK_SIZE = 8192
    
    @staticmethod
    def compute_file_hash(file_obj) -> str:
        """
        Compute SHA-256 hash of file content.
        Args:
            file_obj: Django UploadedFile or File object
        Returns:
            64-character hexadecimal hash string
        Raises:
            FileHashError: If file reading or hash computation fails
        """
        try:
            sha256_hash = hashlib.sha256()
            file_obj.seek(0)
            while chunk := file_obj.read(DeduplicationService.CHUNK_SIZE):
                sha256_hash.update(chunk)
            file_obj.seek(0)
            hash_value = sha256_hash.hexdigest()
            logger.debug(f"Successfully computed hash: {hash_value[:16]}... for file")
            return hash_value
        except (IOError, OSError) as e:
            error_msg = f"Failed to read file during hash computation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FileHashError(error_msg) from e
        except AttributeError as e:
            error_msg = f"Invalid file object provided for hash computation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FileHashError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during hash computation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FileHashError(error_msg) from e
    
    @staticmethod
    def find_duplicate(file_hash: str) -> Optional[File]:
        """
        Find existing file with matching hash.
        Args:
            file_hash: SHA-256 hash string to search for
        Returns:
            File instance if duplicate found, None otherwise
        Raises:
            DuplicateDetectionError: If database query fails
        """
        try:
            if not file_hash or not isinstance(file_hash, str):
                error_msg = f"Invalid file hash provided: {file_hash}"
                logger.error(error_msg)
                raise DuplicateDetectionError(error_msg)
            if len(file_hash) != 64:
                error_msg = f"Invalid hash length: expected 64 characters, got {len(file_hash)}"
                logger.warning(error_msg)
                return None
            duplicate = File.objects.filter(
                file_hash=file_hash,
                is_duplicate=False
            ).first()
            if duplicate:
                logger.info(f"Duplicate found for hash {file_hash[:16]}... (File ID: {duplicate.id})")
            else:
                logger.debug(f"No duplicate found for hash {file_hash[:16]}...")
            return duplicate
        except DatabaseError as e:
            error_msg = f"Database error during duplicate detection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DuplicateDetectionError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during duplicate detection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DuplicateDetectionError(error_msg) from e
    
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
            ReferenceCreationError: If reference creation or transaction fails
        """
        try:
            if not original_file:
                error_msg = "Original file cannot be None"
                logger.error(error_msg)
                raise ReferenceCreationError(error_msg)
            if original_file.is_duplicate:
                error_msg = f"Cannot create reference to duplicate file (ID: {original_file.id})"
                logger.error(error_msg)
                raise ReferenceCreationError(error_msg)
            if not filename or not isinstance(filename, str):
                error_msg = f"Invalid filename provided: {filename}"
                logger.error(error_msg)
                raise ReferenceCreationError(error_msg)
            if size < 0:
                error_msg = f"Invalid file size: {size}"
                logger.error(error_msg)
                raise ReferenceCreationError(error_msg)
            logger.info(
                f"Creating duplicate reference for file '{filename}' "
                f"(Original ID: {original_file.id}, Hash: {original_file.file_hash[:16]}...)"
            )
            original_file.reference_count += 1
            original_file.save(update_fields=['reference_count'])
            duplicate_file = File.objects.create(
                file=None,
                original_filename=filename,
                file_type=file_type,
                size=size,
                file_hash=original_file.file_hash,
                is_duplicate=True,
                original_file=original_file,
                reference_count=0
            )
            logger.info(
                f"Successfully created duplicate reference (ID: {duplicate_file.id}). "
                f"Original file now has {original_file.reference_count} references."
            )
            return duplicate_file
        except IntegrityError as e:
            error_msg = f"Database integrity error creating duplicate reference: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ReferenceCreationError(error_msg) from e
        except DatabaseError as e:
            error_msg = f"Database error creating duplicate reference: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ReferenceCreationError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error creating duplicate reference: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ReferenceCreationError(error_msg) from e
    
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
        total_files = File.objects.count()
        unique_files = File.objects.filter(is_duplicate=False).count()
        duplicate_references = File.objects.filter(is_duplicate=True).count()
        storage_saved_bytes = 0
        unique_file_records = File.objects.filter(
            is_duplicate=False,
            reference_count__gt=1
        ).values('size', 'reference_count')
        for record in unique_file_records:
            storage_saved_bytes += record['size'] * (record['reference_count'] - 1)
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
