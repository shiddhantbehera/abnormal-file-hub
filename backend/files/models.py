"""
File model with deduplication support.
"""
import os
import uuid

from django.db import models


def file_upload_path(instance, filename: str) -> str:
    """
    Generate unique file path for uploads.
    
    Args:
        instance: File model instance
        filename: Original filename
        
    Returns:
        Path string in format 'uploads/{uuid}.{extension}'
    """
    ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''
    unique_filename = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
    return os.path.join('uploads', unique_filename)


class File(models.Model):
    """
    File model with deduplication capabilities.
    
    Supports storing file references without duplicating physical storage
    when identical files (by hash) are uploaded multiple times.
    """
    
    # Primary fields
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    file = models.FileField(
        upload_to=file_upload_path,
        null=True,
        blank=True,
        help_text="Physical file storage (null for duplicates)"
    )
    original_filename = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Original name of uploaded file"
    )
    file_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="MIME type of the file"
    )
    size = models.BigIntegerField(
        db_index=True,
        help_text="File size in bytes"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    # Deduplication fields
    file_hash = models.CharField(
        max_length=64,
        db_index=True,
        null=True,
        blank=True,
        help_text="SHA-256 hash of file content"
    )
    reference_count = models.IntegerField(
        default=1,
        help_text="Number of references to this file"
    )
    is_duplicate = models.BooleanField(
        default=False,
        help_text="True if this is a reference to another file"
    )
    original_file = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='duplicates',
        help_text="Reference to original file if this is a duplicate"
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['file_hash', 'is_duplicate']),
            models.Index(fields=['uploaded_at', 'is_duplicate']),
        ]
        verbose_name = 'File'
        verbose_name_plural = 'Files'
    
    def __str__(self) -> str:
        return f"{self.original_filename} ({'duplicate' if self.is_duplicate else 'original'})"
    
    def __repr__(self) -> str:
        return f"<File id={self.id} filename='{self.original_filename}' duplicate={self.is_duplicate}>"
