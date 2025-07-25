"""
HTTP Request Maker for creating and managing HTTP requests
Handles request construction, serialization, and routing
"""
import json
import logging
import time
import threading
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram
from opentelemetry import trace

from .connection_pool import get_connection_pool
from common.property_loader import get_property

# Prometheus metrics
HTTP_REQUESTS_MADE = Counter('http_client_requests_made_total', 'Total HTTP requests made by client', ['method', 'endpoint', 'status'])
HTTP_REQUEST_LATENCY = Histogram('http_client_request_latency_seconds', 'HTTP client request latency', ['endpoint'])
HTTP_REQUEST_ERRORS = Counter('http_client_request_errors_total', 'Total HTTP client request errors', ['error_type'])

logger = logging.getLogger(__name__)

@dataclass
class HTTPRequest:
    """HTTP Request data structure"""
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    data: Optional[Any] = None
    json_data: Optional[Dict[str, Any]] = None
    timeout: Optional[tuple] = None
    retry_count: int = 0
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class HTTPResponse:
    """HTTP Response data structure"""
    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    json_data: Optional[Dict[str, Any]] = None
    elapsed_time: float = 0.0
    url: str = ""
    
    def is_success(self) -> bool:
        """Check if response is successful"""
        return 200 <= self.status_code < 300
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)

class HTTPRequestMaker:
    """
    HTTP Request Maker for creating and sending HTTP requests
    """
    
    def __init__(self):
        self.connection_pool = get_connection_pool()
        self.tracer = trace.get_tracer(__name__)
        self.default_headers = {
            'User-Agent': 'DistributedSearch/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        logger.info("HTTP Request Maker initialized")
    
    def _build_url(self, base_url: str, endpoint: str) -> str:
        """Build full URL from base URL and endpoint"""
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"http://{base_url}"
        return urljoin(base_url, endpoint.lstrip('/'))
    
    def _prepare_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare request headers"""
        headers = self.default_headers.copy()
        if custom_headers:
            headers.update(custom_headers)
        return headers
    
    def _handle_response(self, response, start_time: float, endpoint: str) -> HTTPResponse:
        """Handle and convert requests.Response to HTTPResponse"""
        elapsed = time.time() - start_time
        
        # Try to parse JSON
        json_data = None
        try:
            if response.content:
                json_data = response.json()
        except (json.JSONDecodeError, ValueError):
            pass
        
        http_response = HTTPResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            text=response.text,
            json_data=json_data,
            elapsed_time=elapsed,
            url=response.url
        )
        
        # Record metrics
        HTTP_REQUESTS_MADE.labels(
            method=response.request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        
        HTTP_REQUEST_LATENCY.labels(endpoint=endpoint).observe(elapsed)
        
        return http_response
    
    def make_request(self, request: HTTPRequest) -> HTTPResponse:
        """
        Make HTTP request
        
        Args:
            request: HTTPRequest object
            
        Returns:
            HTTPResponse object
        """
        start_time = time.time()
        endpoint = urlparse(request.url).path or '/'
        
        with self.tracer.start_as_current_span("http_request_maker") as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", request.url)
            
            try:
                # Prepare request parameters
                kwargs = {}
                
                if request.headers:
                    kwargs['headers'] = self._prepare_headers(request.headers)
                else:
                    kwargs['headers'] = self._prepare_headers()
                
                if request.params:
                    kwargs['params'] = request.params
                
                if request.data:
                    kwargs['data'] = request.data
                
                if request.json_data:
                    kwargs['json'] = request.json_data
                
                if request.timeout:
                    kwargs['timeout'] = request.timeout
                
                # Make request using connection pool
                response = self.connection_pool.request(request.method, request.url, **kwargs)
                
                # Handle response
                http_response = self._handle_response(response, start_time, endpoint)
                
                span.set_attribute("http.status_code", http_response.status_code)
                
                logger.debug(f"HTTP {request.method} {request.url} -> {http_response.status_code} ({http_response.elapsed_time:.3f}s)")
                
                return http_response
                
            except Exception as e:
                HTTP_REQUEST_ERRORS.labels(error_type=type(e).__name__).inc()
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                logger.error(f"HTTP {request.method} {request.url} -> Error: {e}")
                raise
    
    def get_file(self, node_address: str, file_name: str) -> HTTPResponse:
        """
        Get file from remote node
        
        Args:
            node_address: Address of remote node (host:port)
            file_name: Name of file to retrieve
            
        Returns:
            HTTPResponse object
        """
        url = self._build_url(node_address, f"/file/{file_name}")
        request = HTTPRequest(method="GET", url=url)
        return self.make_request(request)
    
    def get_all_files(self, node_address: str) -> HTTPResponse:
        """
        Get all files from remote node
        
        Args:
            node_address: Address of remote node (host:port)
            
        Returns:
            HTTPResponse object
        """
        url = self._build_url(node_address, "/files")
        request = HTTPRequest(method="GET", url=url)
        return self.make_request(request)
    
    def add_file(self, node_address: str, file_name: str) -> HTTPResponse:
        """
        Add file to remote node
        
        Args:
            node_address: Address of remote node (host:port)
            file_name: Name of file to add
            
        Returns:
            HTTPResponse object
        """
        url = self._build_url(node_address, "/file")
        request = HTTPRequest(
            method="POST", 
            url=url,
            json_data={"file_name": file_name}
        )
        return self.make_request(request)
    
    def search_file_in_network(self, file_name: str, node_addresses: List[str]) -> List[HTTPResponse]:
        """
        Search for file across multiple nodes
        
        Args:
            file_name: Name of file to search for
            node_addresses: List of node addresses to search
            
        Returns:
            List of HTTPResponse objects
        """
        responses = []
        
        for node_address in node_addresses:
            try:
                response = self.get_file(node_address, file_name)
                responses.append(response)
                
                # If file found, we can optionally break here
                if response.is_success() and response.json_data and response.json_data.get('exists'):
                    logger.info(f"File '{file_name}' found on node {node_address}")
                    
            except Exception as e:
                logger.warning(f"Failed to search file '{file_name}' on node {node_address}: {e}")
        
        return responses
    
    def check_node_health(self, node_address: str) -> HTTPResponse:
        """
        Check health of remote node
        
        Args:
            node_address: Address of remote node (host:port)
            
        Returns:
            HTTPResponse object
        """
        url = self._build_url(node_address, "/health")
        request = HTTPRequest(method="GET", url=url, timeout=(2, 5))  # Short timeout for health check
        return self.make_request(request)

# Global request maker instance
_request_maker = None
_maker_lock = threading.Lock()

def get_request_maker():
    """Get global HTTP request maker instance"""
    global _request_maker
    if _request_maker is None:
        with _maker_lock:
            if _request_maker is None:
                _request_maker = HTTPRequestMaker()
    return _request_maker

def make_http_request(method: str, url: str, **kwargs) -> HTTPResponse:
    """
    Convenience function to make HTTP request
    
    Args:
        method: HTTP method
        url: Request URL
        **kwargs: Additional request arguments
        
    Returns:
        HTTPResponse object
    """
    request = HTTPRequest(method=method.upper(), url=url, **kwargs)
    return get_request_maker().make_request(request)
