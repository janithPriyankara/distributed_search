"""
HTTP Client for distributed search system
Provides high-level interface for HTTP communication with other nodes
"""
import logging
import threading
import time
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace

from .request_maker import get_request_maker, HTTPResponse
from .connection_pool import get_connection_pool
from common.property_loader import get_property
from common.neighbor_table import NeighborTable
from common.routing_table import RoutingTable

# Prometheus metrics
HTTP_CLIENT_REQUESTS = Counter('http_client_requests_total', 'Total HTTP client requests', ['operation', 'status'])
HTTP_CLIENT_LATENCY = Histogram('http_client_latency_seconds', 'HTTP client operation latency', ['operation'])
HTTP_CLIENT_CONCURRENT_REQUESTS = Gauge('http_client_concurrent_requests', 'Number of concurrent HTTP client requests')
HTTP_CLIENT_ERRORS = Counter('http_client_errors_total', 'Total HTTP client errors', ['error_type'])

logger = logging.getLogger(__name__)

class HTTPClient:
    """
    High-level HTTP Client for distributed search operations
    """
    
    def __init__(self, max_workers=5):
        """
        Initialize HTTP Client
        
        Args:
            max_workers: Maximum number of worker threads for concurrent requests
        """
        self.request_maker = get_request_maker()
        self.connection_pool = get_connection_pool()
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tracer = trace.get_tracer(__name__)
        
        # Load neighbor and routing tables (will be initialized elsewhere)
        self.neighbor_table = None
        self.routing_table = None
        
        self.lock = threading.Lock()
        self.active_requests = 0
        
        logger.info(f"HTTP Client initialized with {max_workers} workers")
    
    def set_neighbor_table(self, neighbor_table):
        """Set neighbor table reference"""
        self.neighbor_table = neighbor_table
    
    def set_routing_table(self, routing_table):
        """Set routing table reference"""
        self.routing_table = routing_table
    
    def _track_request(self, operation: str):
        """Track concurrent requests"""
        with self.lock:
            self.active_requests += 1
            HTTP_CLIENT_CONCURRENT_REQUESTS.set(self.active_requests)
    
    def _untrack_request(self, operation: str):
        """Untrack concurrent requests"""
        with self.lock:
            self.active_requests -= 1
            HTTP_CLIENT_CONCURRENT_REQUESTS.set(self.active_requests)
    
    def fetch_file_from_node(self, node_address: str, file_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Fetch file from specific node
        
        Args:
            node_address: Address of the node (host:port)
            file_name: Name of the file to fetch
            
        Returns:
            Tuple of (success, response_data)
        """
        start_time = time.time()
        operation = "fetch_file"
        
        self._track_request(operation)
        
        with self.tracer.start_as_current_span("http_client_fetch_file") as span:
            span.set_attribute("node.address", node_address)
            span.set_attribute("file.name", file_name)
            
            try:
                response = self.request_maker.get_file(node_address, file_name)
                
                HTTP_CLIENT_REQUESTS.labels(
                    operation=operation,
                    status='success' if response.is_success() else 'failure'
                ).inc()
                
                span.set_attribute("http.status_code", response.status_code)
                
                if response.is_success() and response.json_data:
                    logger.info(f"Successfully fetched file '{file_name}' from {node_address}")
                    return True, response.json_data
                else:
                    logger.warning(f"Failed to fetch file '{file_name}' from {node_address}: HTTP {response.status_code}")
                    return False, None
                    
            except Exception as e:
                HTTP_CLIENT_ERRORS.labels(error_type=type(e).__name__).inc()
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                logger.error(f"Error fetching file '{file_name}' from {node_address}: {e}")
                return False, None
                
            finally:
                self._untrack_request(operation)
                HTTP_CLIENT_LATENCY.labels(operation=operation).observe(time.time() - start_time)
    
    def fetch_all_files_from_node(self, node_address: str) -> Tuple[bool, Optional[List[str]]]:
        """
        Fetch all files list from specific node
        
        Args:
            node_address: Address of the node (host:port)
            
        Returns:
            Tuple of (success, files_list)
        """
        start_time = time.time()
        operation = "fetch_all_files"
        
        self._track_request(operation)
        
        with self.tracer.start_as_current_span("http_client_fetch_all_files") as span:
            span.set_attribute("node.address", node_address)
            
            try:
                response = self.request_maker.get_all_files(node_address)
                
                HTTP_CLIENT_REQUESTS.labels(
                    operation=operation,
                    status='success' if response.is_success() else 'failure'
                ).inc()
                
                span.set_attribute("http.status_code", response.status_code)
                
                if response.is_success() and response.json_data:
                    files = response.json_data.get('files', [])
                    logger.info(f"Successfully fetched {len(files)} files from {node_address}")
                    return True, files
                else:
                    logger.warning(f"Failed to fetch files from {node_address}: HTTP {response.status_code}")
                    return False, None
                    
            except Exception as e:
                HTTP_CLIENT_ERRORS.labels(error_type=type(e).__name__).inc()
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                logger.error(f"Error fetching files from {node_address}: {e}")
                return False, None
                
            finally:
                self._untrack_request(operation)
                HTTP_CLIENT_LATENCY.labels(operation=operation).observe(time.time() - start_time)
    
    def add_file_to_node(self, node_address: str, file_name: str) -> bool:
        """
        Add file to specific node
        
        Args:
            node_address: Address of the node (host:port)
            file_name: Name of the file to add
            
        Returns:
            Success status
        """
        start_time = time.time()
        operation = "add_file"
        
        self._track_request(operation)
        
        with self.tracer.start_as_current_span("http_client_add_file") as span:
            span.set_attribute("node.address", node_address)
            span.set_attribute("file.name", file_name)
            
            try:
                response = self.request_maker.add_file(node_address, file_name)
                
                HTTP_CLIENT_REQUESTS.labels(
                    operation=operation,
                    status='success' if response.is_success() else 'failure'
                ).inc()
                
                span.set_attribute("http.status_code", response.status_code)
                
                if response.is_success():
                    logger.info(f"Successfully added file '{file_name}' to {node_address}")
                    return True
                else:
                    logger.warning(f"Failed to add file '{file_name}' to {node_address}: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                HTTP_CLIENT_ERRORS.labels(error_type=type(e).__name__).inc()
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                logger.error(f"Error adding file '{file_name}' to {node_address}: {e}")
                return False
                
            finally:
                self._untrack_request(operation)
                HTTP_CLIENT_LATENCY.labels(operation=operation).observe(time.time() - start_time)
    
    def search_file_in_network(self, file_name: str, max_nodes: int = 10) -> List[Dict[str, Any]]:
        """
        Search for file across the network using concurrent requests
        
        Args:
            file_name: Name of the file to search for
            max_nodes: Maximum number of nodes to search concurrently
            
        Returns:
            List of results with node information and file status
        """
        start_time = time.time()
        operation = "search_network"
        
        # Get list of nodes to search
        node_addresses = self._get_search_nodes(max_nodes)
        if not node_addresses:
            logger.warning("No nodes available for network search")
            return []
        
        logger.info(f"Searching for file '{file_name}' across {len(node_addresses)} nodes")
        
        with self.tracer.start_as_current_span("http_client_search_network") as span:
            span.set_attribute("file.name", file_name)
            span.set_attribute("nodes.count", len(node_addresses))
            
            results = []
            
            # Submit concurrent requests
            future_to_node = {}
            for node_address in node_addresses:
                future = self.executor.submit(self.fetch_file_from_node, node_address, file_name)
                future_to_node[future] = node_address
            
            # Collect results
            found_count = 0
            for future in as_completed(future_to_node, timeout=30):  # 30 second timeout
                node_address = future_to_node[future]
                try:
                    success, data = future.result()
                    result = {
                        'node_address': node_address,
                        'success': success,
                        'file_exists': False,
                        'data': data
                    }
                    
                    if success and data and data.get('exists'):
                        result['file_exists'] = True
                        found_count += 1
                        logger.info(f"File '{file_name}' found on node {node_address}")
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error searching file '{file_name}' on node {node_address}: {e}")
                    results.append({
                        'node_address': node_address,
                        'success': False,
                        'file_exists': False,
                        'error': str(e)
                    })
            
            span.set_attribute("search.results_count", len(results))
            span.set_attribute("search.found_count", found_count)
            
            HTTP_CLIENT_LATENCY.labels(operation=operation).observe(time.time() - start_time)
            
            logger.info(f"Network search for '{file_name}' completed: found on {found_count}/{len(results)} nodes")
            
            return results
    
    def check_network_health(self, max_nodes: int = 5) -> Dict[str, Any]:
        """
        Check health of nodes in the network
        
        Args:
            max_nodes: Maximum number of nodes to check
            
        Returns:
            Network health summary
        """
        start_time = time.time()
        operation = "health_check"
        
        node_addresses = self._get_search_nodes(max_nodes)
        if not node_addresses:
            return {'healthy_nodes': 0, 'total_nodes': 0, 'nodes': []}
        
        with self.tracer.start_as_current_span("http_client_health_check") as span:
            span.set_attribute("nodes.count", len(node_addresses))
            
            results = []
            healthy_count = 0
            
            # Submit concurrent health checks
            future_to_node = {}
            for node_address in node_addresses:
                future = self.executor.submit(self._check_single_node_health, node_address)
                future_to_node[future] = node_address
            
            # Collect results
            for future in as_completed(future_to_node, timeout=10):  # 10 second timeout
                node_address = future_to_node[future]
                try:
                    is_healthy, response_time = future.result()
                    results.append({
                        'node_address': node_address,
                        'healthy': is_healthy,
                        'response_time': response_time
                    })
                    if is_healthy:
                        healthy_count += 1
                        
                except Exception as e:
                    results.append({
                        'node_address': node_address,
                        'healthy': False,
                        'error': str(e)
                    })
            
            health_summary = {
                'healthy_nodes': healthy_count,
                'total_nodes': len(results),
                'health_percentage': (healthy_count / len(results) * 100) if results else 0,
                'nodes': results
            }
            
            span.set_attribute("health.healthy_nodes", healthy_count)
            span.set_attribute("health.total_nodes", len(results))
            
            HTTP_CLIENT_LATENCY.labels(operation=operation).observe(time.time() - start_time)
            
            return health_summary
    
    def _check_single_node_health(self, node_address: str) -> Tuple[bool, float]:
        """Check health of single node"""
        start_time = time.time()
        try:
            response = self.request_maker.check_node_health(node_address)
            response_time = time.time() - start_time
            return response.is_success(), response_time
        except Exception:
            response_time = time.time() - start_time
            return False, response_time
    
    def _get_search_nodes(self, max_nodes: int) -> List[str]:
        """
        Get list of node addresses to search
        
        Args:
            max_nodes: Maximum number of nodes to return
            
        Returns:
            List of node addresses
        """
        nodes = []
        
        # Try to get nodes from neighbor table first
        if self.neighbor_table:
            neighbors = self.neighbor_table.get_all_neighbors()[:max_nodes]
            nodes.extend([f"{n.get('host', 'localhost')}:{n.get('port', 8080)}" for n in neighbors])
        
        # If we don't have enough nodes, add some default ones for testing
        if len(nodes) < max_nodes:
            # Add localhost with different ports for testing
            test_ports = [8081, 8082, 8083, 8084, 8085]
            for port in test_ports[:max_nodes - len(nodes)]:
                nodes.append(f"127.0.0.1:{port}")
        
        return nodes[:max_nodes]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get HTTP client statistics"""
        return {
            'max_workers': self.max_workers,
            'active_requests': self.active_requests,
            'connection_pool_stats': self.connection_pool.get_stats()
        }
    
    def shutdown(self):
        """Shutdown HTTP client"""
        self.executor.shutdown(wait=True)
        logger.info("HTTP Client shutdown completed")

# Global HTTP client instance
_http_client = None
_client_lock = threading.Lock()

def get_http_client():
    """Get global HTTP client instance"""
    global _http_client
    if _http_client is None:
        with _client_lock:
            if _http_client is None:
                _http_client = HTTPClient()
    return _http_client

def shutdown_http_client():
    """Shutdown global HTTP client"""
    global _http_client
    if _http_client:
        _http_client.shutdown()
        _http_client = None
