"""
File management views with deduplication and search capabilities.
"""
import logging
import time
from typing import Dict, Any

from django.db import connection
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request

from .models import File
from .serializers import FileSerializer
from .services.deduplication import (
    DeduplicationService,
    FileHashError,
    DuplicateDetectionError,
    ReferenceCreationError
)
from .services.search import SearchService, SearchValidationError

logger = logging.getLogger('files.performance')

class FileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for file operations with deduplication support.
    
    Provides CRUD operations plus custom actions for search and storage statistics.
    """
    queryset = File.objects.select_related('original_file').all()
    serializer_class = FileSerializer

    def _log_performance(self, operation: str, start_time: float, 
                        initial_query_count: int, **extra_info) -> None:
        """Log performance metrics for database operations."""
        execution_time = (time.time() - start_time) * 1000
        query_count = len(connection.queries) - initial_query_count
        
        log_data = {
            'operation': operation,
            'queries': query_count,
            'time_ms': f"{execution_time:.2f}",
            **extra_info
        }
        logger.info(f"Performance: {log_data}")

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List all files with performance monitoring."""
        start_time = time.time()
        initial_query_count = len(connection.queries)
        
        response = super().list(request, *args, **kwargs)
        
        self._log_performance('list', start_time, initial_query_count)
        return response

    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Upload a file with automatic deduplication.
        
        If a duplicate is detected, creates a reference instead of storing the file again.
        """
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Compute file hash
        try:
            file_hash = DeduplicationService.compute_file_hash(file_obj)
        except FileHashError as e:
            logger.error(f"Hash computation failed: {e}")
            return self._error_response(
                'Failed to process file',
                'Unable to compute file hash. The file may be corrupted.',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Check for duplicates
        try:
            existing_file = DeduplicationService.find_duplicate(file_hash)
        except DuplicateDetectionError as e:
            logger.error(f"Duplicate detection failed: {e}")
            existing_file = None
        
        # Handle duplicate or unique file
        if existing_file:
            return self._handle_duplicate_file(existing_file, file_obj)
        return self._handle_unique_file(file_obj, file_hash)

    def _handle_duplicate_file(self, existing_file: File, file_obj) -> Response:
        """Create a reference to an existing file."""
        try:
            duplicate_file = DeduplicationService.create_duplicate_reference(
                original_file=existing_file,
                filename=file_obj.name,
                file_type=file_obj.content_type,
                size=file_obj.size
            )
            
            serializer = self.get_serializer(duplicate_file)
            response_data = {
                **serializer.data,
                'is_duplicate': True,
                'storage_saved': file_obj.size
            }
            
            headers = self.get_success_headers(response_data)
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
            
        except ReferenceCreationError as e:
            logger.error(f"Failed to create duplicate reference: {e}")
            return self._error_response(
                'Failed to create file reference',
                'Unable to create duplicate file reference.',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _handle_unique_file(self, file_obj, file_hash: str) -> Response:
        """Store a new unique file."""
        try:
            data = {
                'file': file_obj,
                'original_filename': file_obj.name,
                'file_type': file_obj.content_type,
                'size': file_obj.size,
                'file_hash': file_hash
            }
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            response_data = {
                **serializer.data,
                'is_duplicate': False,
                'storage_saved': 0
            }
            
            headers = self.get_success_headers(response_data)
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            logger.error(f"Failed to save unique file: {e}", exc_info=True)
            return self._error_response(
                'Failed to save file',
                'Unable to save file to storage.',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _error_response(self, error: str, detail: str, 
                       status_code: int) -> Response:
        """Create a standardized error response."""
        return Response(
            {'error': error, 'detail': detail},
            status=status_code
        )

    @action(detail=False, methods=['get'])
    def search(self, request: Request) -> Response:
        """
        Search and filter files based on multiple criteria.
        
        Query Parameters:
            - search: Filename search term (partial, case-insensitive)
            - file_types: Comma-separated list of file types (MIME types)
            - min_size: Minimum file size in bytes
            - max_size: Maximum file size in bytes
            - start_date: Start date for upload date range (ISO 8601)
            - end_date: End date for upload date range (ISO 8601)
        """
        start_time = time.time()
        initial_query_count = len(connection.queries)
        
        # Parse and validate filters
        filters = self._parse_search_filters(request.query_params)
        if isinstance(filters, Response):  # Error response
            return filters
        
        try:
            queryset = self.get_queryset()
            filtered_queryset = SearchService.build_search_query(queryset, filters)
            
            # Paginate results
            page = self.paginate_queryset(filtered_queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response = self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(filtered_queryset, many=True)
                response = Response(serializer.data)
            
            # Log performance
            result_count = len(page) if page else filtered_queryset.count()
            self._log_performance(
                'search', start_time, initial_query_count,
                filters=filters, results=result_count
            )
            
            return response
            
        except (SearchValidationError, ValueError) as e:
            logger.warning(f"Search validation error: {e}")
            return self._error_response(
                'Invalid search parameters',
                str(e),
                status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected search error: {e}", exc_info=True)
            return self._error_response(
                'Search failed',
                'An unexpected error occurred.',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _parse_search_filters(self, params) -> Dict[str, Any]:
        """Parse and validate search filter parameters."""
        filters = {}
        
        # Search term
        if search_term := params.get('search'):
            filters['search'] = search_term
        
        # File types
        if file_types_param := params.get('file_types'):
            filters['file_types'] = [
                ft.strip() for ft in file_types_param.split(',') if ft.strip()
            ]
        
        # Size filters
        for size_param in ['min_size', 'max_size']:
            if value := params.get(size_param):
                try:
                    filters[size_param] = int(value)
                except ValueError:
                    return self._error_response(
                        f'Invalid {size_param} parameter',
                        'Must be an integer.',
                        status.HTTP_400_BAD_REQUEST
                    )
        
        # Date filters
        for date_param in ['start_date', 'end_date']:
            if value := params.get(date_param):
                filters[date_param] = value
        
        return filters

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve a single file with performance monitoring."""
        start_time = time.time()
        initial_query_count = len(connection.queries)
        
        response = super().retrieve(request, *args, **kwargs)
        
        self._log_performance(
            'retrieve', start_time, initial_query_count,
            file_id=kwargs.get('pk')
        )
        
        return response

    @action(detail=False, methods=['get'])
    def storage_stats(self, request: Request) -> Response:
        """
        Get storage savings statistics from deduplication.
        
        Returns statistics including total files, unique files, duplicates, and storage saved.
        """
        try:
            stats = DeduplicationService.calculate_storage_savings()
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to calculate storage statistics: {e}", exc_info=True)
            return self._error_response(
                'Failed to retrieve storage statistics',
                'Unable to calculate storage savings.',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """
        Delete a file with reference counting support.
        
        Handles both duplicate references and original files with proper cleanup.
        """
        instance = self.get_object()
        
        if instance.is_duplicate:
            return self._delete_duplicate(instance)
        return self._delete_original(instance)

    def _delete_duplicate(self, instance: File) -> Response:
        """Delete a duplicate file reference."""
        if instance.original_file:
            original = instance.original_file
            original.reference_count -= 1
            original.save(update_fields=['reference_count'])
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _delete_original(self, instance: File) -> Response:
        """Delete an original file, handling reference counting."""
        if instance.reference_count > 1:
            instance.reference_count -= 1
            instance.save(update_fields=['reference_count'])
            return Response(
                {'message': 'Reference count decremented. File will be deleted when all references are removed.'},
                status=status.HTTP_200_OK
            )
        
        # Delete physical file and database record
        if instance.file:
            instance.file.delete(save=False)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
