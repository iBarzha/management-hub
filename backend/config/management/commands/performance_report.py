from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import json

from config.monitoring import monitor, get_system_metrics
from config.db_pool import pool_manager
from config.websocket_optimizations import get_websocket_stats


class Command(BaseCommand):
    help = 'Generate a comprehensive performance report'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Number of hours to include in the report (default: 24)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='console',
            choices=['console', 'json', 'file'],
            help='Output format (default: console)'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Output file path (required if output=file)'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        output_format = options['output']
        output_file = options['file']
        
        self.stdout.write(f'Generating performance report for the last {hours} hours...')
        
        # Generate report data
        report_data = self.generate_report(hours)
        
        # Output report
        if output_format == 'console':
            self.output_console_report(report_data)
        elif output_format == 'json':
            self.output_json_report(report_data)
        elif output_format == 'file':
            if not output_file:
                self.stderr.write('Error: --file argument is required when output=file')
                return
            self.output_file_report(report_data, output_file)
        
        self.stdout.write(
            self.style.SUCCESS('Performance report generated successfully!')
        )
    
    def generate_report(self, hours):
        """Generate comprehensive performance report"""
        since = timezone.now() - timedelta(hours=hours)
        
        # System metrics
        system_metrics = get_system_metrics()
        
        # Database metrics
        db_stats = pool_manager.health_check()
        
        # WebSocket metrics
        ws_stats = get_websocket_stats()
        
        # Application metrics
        request_metrics = monitor.get_metrics('request_duration', since=since)
        db_metrics = monitor.get_metrics('database_time', since=since)
        function_metrics = {
            name: metrics for name, metrics in monitor.metrics.items()
            if name.startswith('function_execution:')
        }
        
        # Calculate statistics
        request_stats = self.calculate_stats([m['value'] for m in request_metrics])
        db_stats_calc = self.calculate_stats([m['value'] for m in db_metrics])
        
        return {
            'timestamp': timezone.now().isoformat(),
            'period_hours': hours,
            'system_metrics': system_metrics,
            'database': {
                'health': db_stats,
                'query_stats': db_stats_calc,
                'slow_queries': len(monitor.slow_queries),
                'total_queries': len(db_metrics)
            },
            'websocket': ws_stats,
            'application': {
                'request_stats': request_stats,
                'total_requests': len(request_metrics),
                'function_metrics': len(function_metrics),
                'slow_queries': monitor.slow_queries[-10:]  # Last 10 slow queries
            }
        }
    
    def calculate_stats(self, values):
        """Calculate basic statistics for a list of values"""
        if not values:
            return {'count': 0}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'median': sorted(values)[len(values) // 2]
        }
    
    def output_console_report(self, data):
        """Output report to console"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(f"PERFORMANCE REPORT - {data['timestamp']}")
        self.stdout.write('='*60)
        
        # System metrics
        self.stdout.write('\nSYSTEM METRICS:')
        self.stdout.write('-'*20)
        sys_metrics = data['system_metrics']
        self.stdout.write(f"CPU Usage: {sys_metrics.get('cpu_percent', 'N/A')}%")
        self.stdout.write(f"Memory Usage: {sys_metrics.get('memory_percent', 'N/A')}%")
        self.stdout.write(f"Disk Usage: {sys_metrics.get('disk_percent', 'N/A')}%")
        self.stdout.write(f"Database Connections: {sys_metrics.get('database_connections', 'N/A')}")
        
        # Application metrics
        self.stdout.write('\nAPPLICATION METRICS:')
        self.stdout.write('-'*20)
        app_metrics = data['application']
        self.stdout.write(f"Total Requests: {app_metrics['total_requests']}")
        
        if app_metrics['request_stats']['count'] > 0:
            req_stats = app_metrics['request_stats']
            self.stdout.write(f"Average Response Time: {req_stats['avg']:.3f}s")
            self.stdout.write(f"Max Response Time: {req_stats['max']:.3f}s")
            self.stdout.write(f"Min Response Time: {req_stats['min']:.3f}s")
        
        # Database metrics
        self.stdout.write('\nDATABASE METRICS:')
        self.stdout.write('-'*20)
        db_metrics = data['database']
        self.stdout.write(f"Total Queries: {db_metrics['total_queries']}")
        self.stdout.write(f"Slow Queries: {db_metrics['slow_queries']}")
        
        if db_metrics['query_stats']['count'] > 0:
            query_stats = db_metrics['query_stats']
            self.stdout.write(f"Average Query Time: {query_stats['avg']:.3f}s")
            self.stdout.write(f"Max Query Time: {query_stats['max']:.3f}s")
        
        # WebSocket metrics
        self.stdout.write('\nWEBSOCKET METRICS:')
        self.stdout.write('-'*20)
        ws_metrics = data['websocket']
        self.stdout.write(f"Total Connections: {ws_metrics['total_connections']}")
        self.stdout.write(f"Active Groups: {ws_metrics['active_groups']}")
        self.stdout.write(f"User Connections: {ws_metrics['user_connections']}")
        
        self.stdout.write('\n' + '='*60)
    
    def output_json_report(self, data):
        """Output report as JSON"""
        json_output = json.dumps(data, indent=2, default=str)
        self.stdout.write(json_output)
    
    def output_file_report(self, data, filepath):
        """Output report to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.stdout.write(f'Report saved to {filepath}')
        except Exception as e:
            self.stderr.write(f'Error saving report to file: {str(e)}')