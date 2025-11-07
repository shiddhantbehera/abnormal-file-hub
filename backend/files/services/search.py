from django.db.models import QuerySet, Q
from datetime import datetime
from typing import Optional, List


class SearchValidationError(Exception):
    """Custom exception for search parameter validation errors"""
    pass


class SearchService:
    """Service for building and executing search queries on File model"""
    
    @staticmethod
    def validate_filters(filters: dict) -> None:
        """
        Validate filter parameters before applying them.
        
        Args:
            filters: Dictionary containing filter parameters
        
        Raises:
            SearchValidationError: If any filter parameter is invalid
        """
        # Validate size range
        min_size = filters.get('min_size')
        max_size = filters.get('max_size')
        
        if min_size is not None:
            if not isinstance(min_size, (int, float)) or min_size < 0:
                raise SearchValidationError("min_size must be a non-negative number")
        
        if max_size is not None:
            if not isinstance(max_size, (int, float)) or max_size < 0:
                raise SearchValidationError("max_size must be a non-negative number")
        
        if min_size is not None and max_size is not None:
            if min_size > max_size:
                raise SearchValidationError("min_size cannot be greater than max_size")
        
        # Validate date range
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError, TypeError):
                raise SearchValidationError(
                    f"Invalid start_date format: '{start_date}'. Expected ISO 8601 format (e.g., '2025-11-06T10:30:00Z')"
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError, TypeError):
                raise SearchValidationError(
                    f"Invalid end_date format: '{end_date}'. Expected ISO 8601 format (e.g., '2025-11-06T10:30:00Z')"
                )
        
        if start_date and end_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if start_dt > end_dt:
                    raise SearchValidationError("start_date cannot be after end_date")
            except SearchValidationError:
                raise
            except Exception:
                pass  # Already validated individual dates above
        
        # Validate file types
        file_types = filters.get('file_types')
        if file_types is not None:
            if not isinstance(file_types, list):
                raise SearchValidationError("file_types must be a list")
            if not all(isinstance(ft, str) for ft in file_types):
                raise SearchValidationError("All file_types must be strings")
        
        # Validate search term
        search = filters.get('search')
        if search is not None and not isinstance(search, str):
            raise SearchValidationError("search must be a string")
    
    @staticmethod
    def build_search_query(queryset: QuerySet, filters: dict) -> QuerySet:
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
        
        # Apply filename filter
        if filters.get('search'):
            queryset = SearchService.apply_filename_filter(
                queryset, 
                filters['search']
            )
        
        # Apply file type filter
        if filters.get('file_types'):
            queryset = SearchService.apply_filetype_filter(
                queryset, 
                filters['file_types']
            )
        
        # Apply size range filter
        min_size = filters.get('min_size')
        max_size = filters.get('max_size')
        if min_size is not None or max_size is not None:
            queryset = SearchService.apply_size_filter(
                queryset, 
                min_size, 
                max_size
            )
        
        # Apply date range filter
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        if start_date or end_date:
            queryset = SearchService.apply_date_filter(
                queryset, 
                start_date, 
                end_date
            )
        
        return queryset
    
    @staticmethod
    def apply_filename_filter(queryset: QuerySet, search_term: str) -> QuerySet:
        """
        Filter by filename using case-insensitive partial matching.
        
        Args:
            queryset: QuerySet to filter
            search_term: Text to search for in filename
        
        Returns:
            Filtered QuerySet
        """
        return queryset.filter(original_filename__icontains=search_term)
    
    @staticmethod
    def apply_filetype_filter(queryset: QuerySet, file_types: List[str]) -> QuerySet:
        """
        Filter by one or more file types.
        
        Args:
            queryset: QuerySet to filter
            file_types: List of file types (MIME types or extensions)
        
        Returns:
            Filtered QuerySet
        """
        return queryset.filter(file_type__in=file_types)
    
    @staticmethod
    def apply_size_filter(
        queryset: QuerySet, 
        min_size: Optional[int], 
        max_size: Optional[int]
    ) -> QuerySet:
        """
        Filter by file size range.
        
        Args:
            queryset: QuerySet to filter
            min_size: Minimum file size in bytes (optional)
            max_size: Maximum file size in bytes (optional)
        
        Returns:
            Filtered QuerySet
        """
        if min_size is not None:
            queryset = queryset.filter(size__gte=min_size)
        
        if max_size is not None:
            queryset = queryset.filter(size__lte=max_size)
        
        return queryset
    
    @staticmethod
    def apply_date_filter(
        queryset: QuerySet, 
        start_date: Optional[str], 
        end_date: Optional[str]
    ) -> QuerySet:
        """
        Filter by upload date range.
        
        Args:
            queryset: QuerySet to filter
            start_date: Start date in ISO 8601 format (optional)
            end_date: End date in ISO 8601 format (optional)
        
        Returns:
            Filtered QuerySet
        
        Note:
            Date validation is performed in validate_filters() before this method is called.
        """
        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            queryset = queryset.filter(uploaded_at__gte=start_datetime)
        
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            queryset = queryset.filter(uploaded_at__lte=end_datetime)
        
        return queryset
