"""
HTTP Connection Pool for managing persistent HTTP connections
Provides connection pooling, retry logic, and connection management
"""
import threading
import time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace
import logging

# Prometheus metrics
CONNECTION_POOL_REQUESTS = Counter('http_connection_pool_requests_total', 'Total HTTP connection pool requests', ['method', 'status'])
CONNECTION_POOL_LATENCY = Histogram('http_connection_pool_latency_seconds', 'HTTP connection pool request latency')
ACTIVE_CONNECTIONS = Gauge('http_connection_pool_active_connections', 'Number of active HTTP connections')
CONNECTION_POOL_ERRORS = Counter('http_connection_pool_errors_total', 'Total HTTP connection pool errors', ['error_type'])

logger = logging.getLogger(__name__)

class HTTPConnectionPool:
    """
    HTTP Connection Pool with retry logic and connection management
    """
    
    def __init__(self, 
                 pool_connections=10, 
                 pool_maxsize=50, 
                 max_retries=3,
                 backoff_factor=0.3,
                 timeout=(5, 30)):
        """
        Initialize HTTP connection pool
        
        Args:
            pool_connections: Number of connection pools
            pool_maxsize: Maximum number of connections per pool
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor for retries
            timeout: Request timeout (connect, read)
        """
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize
        self.timeout = timeout
        self.lock = threading.Lock()
        self.active_connections = 0
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            backoff_factor=backoff_factor
        )
        
        # Create session with connection pool
        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # OpenTelemetry tracing
        self.tracer = trace.get_tracer(__name__)
        
        logger.info(f"HTTP Connection Pool initialized: connections={pool_connections}, maxsize={pool_maxsize}")
    
    def request(self, method, url, **kwargs):
        """
        Make HTTP request using connection pool
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional request arguments
            
        Returns:
            requests.Response object
        """
        start_time = time.time()
        
        with self.tracer.start_as_current_span("http_connection_pool_request") as span:
            span.set_attribute("http.method", method.upper())
            span.set_attribute("http.url", url)
            
            try:
                with self.lock:
                    self.active_connections += 1
                    ACTIVE_CONNECTIONS.set(self.active_connections)
                
                # Set default timeout if not provided
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = self.timeout
                
                # Make request
                response = self.session.request(method, url, **kwargs)
                
                # Record metrics
                CONNECTION_POOL_REQUESTS.labels(
                    method=method.upper(), 
                    status=response.status_code
                ).inc()
                
                span.set_attribute("http.status_code", response.status_code)
                
                logger.debug(f"HTTP {method.upper()} {url} -> {response.status_code}")
                
                return response
                
            except requests.exceptions.Timeout as e:
                CONNECTION_POOL_ERRORS.labels(error_type='timeout').inc()
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                logger.error(f"HTTP {method.upper()} {url} -> Timeout: {e}")
                raise
                
            except requests.exceptions.ConnectionError as e:
                CONNECTION_POOL_ERRORS.labels(error_type='connection_error').inc()
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                logger.error(f"HTTP {method.upper()} {url} -> Connection Error: {e}")
                raise
                
            except requests.exceptions.RequestException as e:
                CONNECTION_POOL_ERRORS.labels(error_type='request_error').inc()
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                logger.error(f"HTTP {method.upper()} {url} -> Request Error: {e}")
                raise
                
            finally:
                with self.lock:
                    self.active_connections -= 1
                    ACTIVE_CONNECTIONS.set(self.active_connections)
                
                # Record latency
                latency = time.time() - start_time
                CONNECTION_POOL_LATENCY.observe(latency)
    
    def get(self, url, **kwargs):
        """Make GET request"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url, **kwargs):
        """Make POST request"""
        return self.request('POST', url, **kwargs)
    
    def put(self, url, **kwargs):
        """Make PUT request"""
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url, **kwargs):
        """Make DELETE request"""
        return self.request('DELETE', url, **kwargs)
    
    def head(self, url, **kwargs):
        """Make HEAD request"""
        return self.request('HEAD', url, **kwargs)
    
    def close(self):
        """Close all connections in the pool"""
        self.session.close()
        logger.info("HTTP Connection Pool closed")
    
    def get_stats(self):
        """Get connection pool statistics"""
        return {
            'pool_connections': self.pool_connections,
            'pool_maxsize': self.pool_maxsize,
            'active_connections': self.active_connections,
            'timeout': self.timeout
        }

# Global connection pool instance
_connection_pool = None
_pool_lock = threading.Lock()

def get_connection_pool():
    """Get global HTTP connection pool instance"""
    global _connection_pool
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = HTTPConnectionPool()
    return _connection_pool

def close_connection_pool():
    """Close global HTTP connection pool"""
    global _connection_pool
    if _connection_pool:
        _connection_pool.close()
        _connection_pool = None
