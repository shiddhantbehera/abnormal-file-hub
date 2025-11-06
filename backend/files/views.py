from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import File
from .serializers import FileSerializer
from .services.deduplication import DeduplicationService
from .services.search import SearchService

# Create your views here.

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Compute file hash before saving
        file_hash = DeduplicationService.compute_file_hash(file_obj)
        
        # Check for existing file with same hash
        existing_file = DeduplicationService.find_duplicate(file_hash)
        
        if existing_file:
            # Duplicate found - create reference instead of storing file
            duplicate_file = DeduplicationService.create_duplicate_reference(
                original_file=existing_file,
                filename=file_obj.name,
                file_type=file_obj.content_type,
                size=file_obj.size
            )
            
            # Serialize the duplicate reference
            serializer = self.get_serializer(duplicate_file)
            response_data = serializer.data
            
            # Add deduplication info to response
            response_data['is_duplicate'] = True
            response_data['storage_saved'] = file_obj.size
            
            headers = self.get_success_headers(response_data)
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            # Unique file - save normally with file_hash
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
            
            # Add deduplication info to response
            response_data['is_duplicate'] = False
            response_data['storage_saved'] = 0
            
            headers = self.get_success_headers(response_data)
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

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
        # Extract filter parameters from query params
        filters = {}
        
        # Filename search
        search_term = request.query_params.get('search')
        if search_term:
            filters['search'] = search_term
        
        # File types (comma-separated)
        file_types_param = request.query_params.get('file_types')
        if file_types_param:
            filters['file_types'] = [ft.strip() for ft in file_types_param.split(',') if ft.strip()]
        
        # Size range
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
        
        # Date range
        start_date = request.query_params.get('start_date')
        if start_date:
            filters['start_date'] = start_date
        
        end_date = request.query_params.get('end_date')
        if end_date:
            filters['end_date'] = end_date
        
        # Build filtered query using SearchService
        try:
            queryset = self.get_queryset()
            filtered_queryset = SearchService.build_search_query(queryset, filters)
            
            # Apply pagination
            page = self.paginate_queryset(filtered_queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            # Fallback if pagination is not configured
            serializer = self.get_serializer(filtered_queryset, many=True)
            return Response(serializer.data)
            
        except ValueError as e:
            # Handle date parsing errors from SearchService
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

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
        stats = DeduplicationService.calculate_storage_savings()
        return Response(stats, status=status.HTTP_200_OK)
