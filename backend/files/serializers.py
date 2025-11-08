"""
Serializers for file models.
"""
from rest_framework import serializers

from .models import File


class FileSerializer(serializers.ModelSerializer):
    """
    Serializer for File model with computed fields.
    
    Includes storage_saved calculation for duplicate files.
    """
    
    is_duplicate = serializers.BooleanField(read_only=True)
    storage_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = File
        fields = [
            'id',
            'file',
            'original_filename',
            'file_type',
            'size',
            'uploaded_at',
            'file_hash',
            'is_duplicate',
            'storage_saved'
        ]
        read_only_fields = ['id', 'uploaded_at', 'is_duplicate']
    
    def get_storage_saved(self, obj: File) -> int:
        """
        Calculate storage saved for duplicate files.
        
        Args:
            obj: File instance
            
        Returns:
            File size if duplicate (storage saved), 0 otherwise
        """
        return obj.size if obj.is_duplicate else 0 