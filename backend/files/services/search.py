from django.db.models import QuerySet, Q
from datetime import datetime
from typing import Optional, List


class SearchService:
    """Service for building and executing search queries on File model"""
    
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
        """
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
        
        Raises:
            ValueError: If date format is invalid
        """
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(uploaded_at__gte=start_datetime)
            except (ValueError, AttributeError) as e:
                raise ValueError(f"Invalid start_date format: {start_date}") from e
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(uploaded_at__lte=end_datetime)
            except (ValueError, AttributeError) as e:
                raise ValueError(f"Invalid end_date format: {end_date}") from e
        
        return queryset
