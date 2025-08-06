from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class OptimizedCursorPagination(CursorPagination):
    """
    Cursor-based pagination for optimal performance with large datasets
    """
    page_size = 20
    max_page_size = 100
    ordering = '-created_at'
    cursor_query_param = 'cursor'
    page_size_query_param = 'page_size'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('count', self.get_count() if hasattr(self, 'get_count') else None)
        ]))


class EnhancedPageNumberPagination(PageNumberPagination):
    """
    Enhanced page-based pagination with performance optimizations
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class TaskPagination(OptimizedCursorPagination):
    """
    Specialized pagination for tasks with filtering support
    """
    page_size = 25
    ordering = '-updated_at'


class ProjectPagination(EnhancedPageNumberPagination):
    """
    Specialized pagination for projects
    """
    page_size = 15


class CommentPagination(OptimizedCursorPagination):
    """
    Specialized pagination for comments
    """
    page_size = 50
    ordering = 'created_at'  # Comments ordered chronologically


class AnalyticsPagination(EnhancedPageNumberPagination):
    """
    Specialized pagination for analytics data
    """
    page_size = 30
    max_page_size = 200