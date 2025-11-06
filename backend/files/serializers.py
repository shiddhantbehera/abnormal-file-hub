from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    is_duplicate = serializers.BooleanField(read_only=True)
    storage_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = File
        fields = ['id', 'file', 'original_filename', 'file_type', 'size', 'uploaded_at', 
                  'file_hash', 'is_duplicate', 'storage_saved']
        read_only_fields = ['id', 'uploaded_at', 'is_duplicate']
    
    def get_storage_saved(self, obj):
        """
        Calculate storage saved for duplicate files.
        For duplicate files, this is the file size (since we didn't store it).
        For unique files, this is 0.
        """
        if obj.is_duplicate:
            return obj.size
        return 0 