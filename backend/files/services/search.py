"""
Search service for file filtering and querying.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from django.db.models import QuerySet


class SearchValidationError(Exception):
    """Custom exception for search parameter validation errors."""
    pass


class SearchService:
    """
    Service for building and executing search queries on File model.
    
    Provides methods for filtering files by name, type, size, and date range.
    """
    
    @staticmethod
    def validate_filters(filters: Dict[str, Any]) -> None:
        """
        Validate filter parameters before applying them.
        
        Args:
            filters: Dictionary containing filter parameters
            
        Raises:
            SearchValidationError: If any filter parameter is invalid
        """
        # Validate size range
        SearchService._validate_size_filters(filters)
        
        # Validate date range
        SearchService._validate_date_filters(filters)
        
        # Validate file types
        if file_types := filters.get('file_types'):
            if not isinstance(file_types, list):
                raise SearchValidationError("file_types must be a list")
            if not all(isinstance(ft, str) for ft in file_types):
                raise SearchValidationError("All file_types must be strings")
        
        # Validate search term
        if search := filters.get('search'):
            if not isinstance(search, str):
                raise SearchValidationError("search must be a string")

    @staticmethod
    def _validate_size_filters(filters: Dict[str, Any]) -> None:
        """Validate size filter parameters."""
        min_size = filters.get('min_size')
        max_size = filters.get('max_size')
        
        if min_size is not None:
            if not isinstance(min_size, (int, float)) or min_size < 0:
                raise SearchValidationError("min_size must be a non-negative number")
        
        if max_size is not None:
            if not isinstance(max_size, (int, float)) or max_size < 0:
                raise SearchValidationError("max_size must be a non-negative number")
        
        if min_size is not None and max_size is not None and min_size > max_size:
            raise SearchValidationError("min_size cannot be greater than max_size")

    @staticmethod
    def _validate_date_filters(filters: Dict[str, Any]) -> None:
        """Validate date filter parameters."""
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError, TypeError) as e:
                raise SearchValidationError(
                    f"Invalid start_date format: '{start_date}'. "
                    f"Expected ISO 8601 format (e.g., '2025-11-06T10:30:00Z')"
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError, TypeError) as e:
                raise SearchValidationError(
                    f"Invalid end_date format: '{end_date}'. "
                    f"Expected ISO 8601 format (e.g., '2025-11-06T10:30:00Z')"
                )
        
        if start_dt and end_dt and start_dt > end_dt:
            raise SearchValidationError("start_date cannot be after end_date")
    
    @staticmethod
    def build_search_query(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """
        Build Django ORM query from filter parameters.
        
        Args:
            queryset: Initial QuerySet to filter
            filters: Dictionary containing filter parameters:
                - search: filename search term
                - file_types: list of file types to filter by
                - min_size: minimum file size in bytes
                - max_size: maximum file size in bytes
                - start_date: start date for upload date range (ISO 8601)
                - end_date: end date for upload date range (ISO 8601)
                
        Returns:
            Filtered QuerySet
            
        Raises:
            SearchValidationError: If any filter parameter is invalid
        """
        # Validate all filters first
        SearchService.validate_filters(filters)
        
        # Apply filters sequentially
        if search := filters.get('search'):
            queryset = queryset.filter(original_filename__icontains=search)
        
        if file_types := filters.get('file_types'):
            queryset = queryset.filter(file_type__in=file_types)
        
        if (min_size := filters.get('min_size')) is not None:
            queryset = queryset.filter(size__gte=min_size)
        
        if (max_size := filters.get('max_size')) is not None:
            queryset = queryset.filter(size__lte=max_size)
        
        if start_date := filters.get('start_date'):
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            queryset = queryset.filter(uploaded_at__gte=start_dt)
        
        if end_date := filters.get('end_date'):
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            queryset = queryset.filter(uploaded_at__lte=end_dt)
        
        return queryset

