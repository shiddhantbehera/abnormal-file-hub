from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import connection
from django.db.models import Prefetch
import logging
import time
from .models import File
from .serializers import FileSerializer
from .services.deduplication import (
    DeduplicationService,
    FileHashError,
    DuplicateDetectionError,
    ReferenceCreationError
)
from .services.search import SearchService, SearchValidationError

# Create your views here.

logger = logging.getLogger('files.performance')

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.select_related('original_file').all()
    serializer_class = FileSerializer

    def list(self, request, *args, **kwargs):
        """
        List all files with performance monitoring.
        """
        start_time = time.time()
        initial_query_count = len(connection.queries)
        response = super().list(request, *args, **kwargs)
        end_time = time.time()
        query_count = len(connection.queries) - initial_query_count
        execution_time = (end_time - start_time) * 1000
        logger.info(
            f"List query executed - "
            f"Queries: {query_count}, "
            f"Time: {execution_time:.2f}ms"
        )
        return response

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            file_hash = DeduplicationService.compute_file_hash(file_obj)
        except FileHashError as e:
            logger.error(f"Hash computation failed for file '{file_obj.name}': {str(e)}")
            return Response(
                {
                    'error': 'Failed to process file',
                    'detail': 'Unable to compute file hash. The file may be corrupted or unreadable.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            existing_file = DeduplicationService.find_duplicate(file_hash)
        except DuplicateDetectionError as e:
            logger.error(f"Duplicate detection failed for hash {file_hash[:16]}...: {str(e)}")
            existing_file = None
        
        if existing_file:
            try:
                duplicate_file = DeduplicationService.create_duplicate_reference(
                    original_file=existing_file,
                    filename=file_obj.name,
                    file_type=file_obj.content_type,
                    size=file_obj.size
                )
                
                serializer = self.get_serializer(duplicate_file)
                response_data = serializer.data
                
                response_data['is_duplicate'] = True
                response_data['storage_saved'] = file_obj.size
                
                headers = self.get_success_headers(response_data)
                return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
                
            except ReferenceCreationError as e:
                logger.error(
                    f"Failed to create duplicate reference for file '{file_obj.name}': {str(e)}"
                )
                return Response(
                    {
                        'error': 'Failed to create file reference',
                        'detail': 'Unable to create duplicate file reference. Please try again.'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
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
                
                response_data = serializer.data
                
                response_data['is_duplicate'] = False
                response_data['storage_saved'] = 0
                
                headers = self.get_success_headers(response_data)
                return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
                
            except Exception as e:
                logger.error(f"Failed to save unique file '{file_obj.name}': {str(e)}", exc_info=True)
                return Response(
                    {
                        'error': 'Failed to save file',
                        'detail': 'Unable to save file to storage. Please try again.'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search and filter files based on multiple criteria.
        
        Query Parameters:
            - search: Filename search term (partial, case-insensitive)
            - file_types: Comma-separated list of file types (MIME types)
            - min_size: Minimum file size in bytes
            - max_size: Maximum file size in bytes
            - start_date: Start date for upload date range (ISO 8601)
            - end_date: End date for upload date range (ISO 8601)
        
        Returns:
            Paginated response with filtered file results
        """
        start_time = time.time()
        initial_query_count = len(connection.queries)
        filters = {}
        
        search_term = request.query_params.get('search')
        if search_term:
            filters['search'] = search_term
        
        file_types_param = request.query_params.get('file_types')
        if file_types_param:
            filters['file_types'] = [ft.strip() for ft in file_types_param.split(',') if ft.strip()]
        
        min_size = request.query_params.get('min_size')
        if min_size:
            try:
                filters['min_size'] = int(min_size)
            except ValueError:
                return Response(
                    {'error': 'Invalid min_size parameter. Must be an integer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        max_size = request.query_params.get('max_size')
        if max_size:
            try:
                filters['max_size'] = int(max_size)
            except ValueError:
                return Response(
                    {'error': 'Invalid max_size parameter. Must be an integer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        start_date = request.query_params.get('start_date')
        if start_date:
            filters['start_date'] = start_date
        
        end_date = request.query_params.get('end_date')
        if end_date:
            filters['end_date'] = end_date
        
        try:
            queryset = self.get_queryset()
            filtered_queryset = SearchService.build_search_query(queryset, filters)
            
            page = self.paginate_queryset(filtered_queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response = self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(filtered_queryset, many=True)
                response = Response(serializer.data)
            
            end_time = time.time()
            query_count = len(connection.queries) - initial_query_count
            execution_time = (end_time - start_time) * 1000
            
            logger.info(
                f"Search query executed - "
                f"Filters: {filters}, "
                f"Queries: {query_count}, "
                f"Time: {execution_time:.2f}ms, "
                f"Results: {filtered_queryset.count() if page is None else len(page)}"
            )
            
            return response
            
        except SearchValidationError as e:
            logger.warning(f"Search validation error: {str(e)}")
            return Response(
                {
                    'error': 'Invalid search parameters',
                    'detail': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            logger.warning(f"Search value error: {str(e)}")
            return Response(
                {
                    'error': 'Invalid search parameters',
                    'detail': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error during search: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Search failed',
                    'detail': 'An unexpected error occurred while processing your search. Please try again.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single file with performance monitoring.
        """
        start_time = time.time()
        initial_query_count = len(connection.queries)
        
        response = super().retrieve(request, *args, **kwargs)
        
        end_time = time.time()
        query_count = len(connection.queries) - initial_query_count
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        logger.info(
            f"Retrieve query executed - "
            f"ID: {kwargs.get('pk')}, "
            f"Queries: {query_count}, "
            f"Time: {execution_time:.2f}ms"
        )
        
        return response

    @action(detail=False, methods=['get'])
    def storage_stats(self, request):
        """
        Get storage savings statistics from deduplication.
        
        Returns:
            JSON response containing:
                - total_files: Total number of file records
                - unique_files: Number of unique files (non-duplicates)
                - duplicate_references: Number of duplicate references
                - storage_saved_bytes: Total bytes saved
                - storage_saved_readable: Human-readable format (e.g., "50.00 MB")
        """
        try:
            stats = DeduplicationService.calculate_storage_savings()
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to calculate storage statistics: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Failed to retrieve storage statistics',
                    'detail': 'Unable to calculate storage savings. Please try again later.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """
        Delete a file with reference counting support.
        
        Behavior:
            - If deleting a duplicate reference: decrement reference_count on original file
            - If deleting an original file with reference_count > 1: only delete when count reaches 0
            - If deleting an original file: cascade delete all duplicate references (handled by FK)
            - Only delete physical file when reference_count reaches 0
        """
        instance = self.get_object()
        if instance.is_duplicate:
            if instance.original_file:
                original = instance.original_file
                original.reference_count -= 1
                original.save(update_fields=['reference_count'])
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            if instance.reference_count > 1:
                instance.reference_count -= 1
                instance.save(update_fields=['reference_count'])
                return Response(
                    {'message': 'Reference count decremented. File will be deleted when all references are removed.'},
                    status=status.HTTP_200_OK
                )
            else:
                if instance.file:
                    instance.file.delete(save=False)
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
