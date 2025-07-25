#!/usr/bin/env python3
"""
HTTP Client Test Script
Tests HTTP connection pool, request maker, and client functionality
"""
import sys
import time
import json
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our HTTP components
from http_local.client import get_http_client, shutdown_http_client
from http_local.request_maker import get_request_maker, HTTPRequest
from http_local.connection_pool import get_connection_pool

def test_connection_pool():
    """Test HTTP connection pool functionality"""
    print("\n🔧 Testing HTTP Connection Pool...")
    
    pool = get_connection_pool()
    
    # Test basic GET request
    try:
        response = pool.get('http://httpbin.org/json')
        print(f"✅ Connection pool GET test: {response.status_code}")
        print(f"   Response size: {len(response.content)} bytes")
        
        # Test connection pool stats
        stats = pool.get_stats()
        print(f"✅ Connection pool stats: {stats}")
        
    except Exception as e:
        print(f"❌ Connection pool test failed: {e}")

def test_request_maker():
    """Test HTTP request maker functionality"""
    print("\n📡 Testing HTTP Request Maker...")
    
    request_maker = get_request_maker()
    
    try:
        # Test local server health check
        local_url = "http://127.0.0.1:8080"
        
        # Test health endpoint
        health_request = HTTPRequest(
            method="GET",
            url=f"{local_url}/health"
        )
        
        health_response = request_maker.make_request(health_request)
        print(f"✅ Health check: {health_response.status_code}")
        if health_response.json_data:
            print(f"   Health data: {health_response.json_data}")
        
        # Test files endpoint
        files_response = request_maker.get_all_files("127.0.0.1:8080")
        print(f"✅ Get all files: {files_response.status_code}")
        if files_response.json_data:
            files = files_response.json_data.get('files', [])
            print(f"   Found {len(files)} files: {files[:5]}...")  # Show first 5
        
        # Test get specific file
        if files_response.json_data and files_response.json_data.get('files'):
            test_file = files_response.json_data['files'][0]
            file_response = request_maker.get_file("127.0.0.1:8080", test_file)
            print(f"✅ Get file '{test_file}': {file_response.status_code}")
            if file_response.json_data:
                exists = file_response.json_data.get('exists', False)
                print(f"   File exists: {exists}")
        
    except Exception as e:
        print(f"❌ Request maker test failed: {e}")

def test_http_client():
    """Test HTTP client functionality"""
    print("\n🌐 Testing HTTP Client...")
    
    client = get_http_client()
    
    try:
        # Test fetch file from local node
        success, data = client.fetch_file_from_node("127.0.0.1:8080", "alpha.txt")
        print(f"✅ Fetch file test: success={success}")
        if data:
            print(f"   File data: exists={data.get('exists', False)}")
        
        # Test fetch all files
        success, files = client.fetch_all_files_from_node("127.0.0.1:8080")
        print(f"✅ Fetch all files test: success={success}")
        if files:
            print(f"   Files count: {len(files)}")
        
        # Test add file
        success = client.add_file_to_node("127.0.0.1:8080", "test_file.txt")
        print(f"✅ Add file test: success={success}")
        
        # Test network health check
        health_summary = client.check_network_health(max_nodes=3)
        print(f"✅ Network health check:")
        print(f"   Healthy nodes: {health_summary['healthy_nodes']}/{health_summary['total_nodes']}")
        print(f"   Health percentage: {health_summary['health_percentage']:.1f}%")
        
        # Test network search (will test against localhost and some mock addresses)
        print("\n🔍 Testing network file search...")
        search_results = client.search_file_in_network("alpha.txt", max_nodes=3)
        print(f"✅ Network search completed: {len(search_results)} nodes searched")
        
        found_nodes = [r for r in search_results if r.get('file_exists')]
        print(f"   File found on {len(found_nodes)} nodes")
        
        for result in search_results:
            status = "✅ Found" if result.get('file_exists') else "❌ Not found"
            print(f"   {result['node_address']}: {status}")
        
        # Get client stats
        stats = client.get_stats()
        print(f"✅ Client stats: {stats}")
        
    except Exception as e:
        print(f"❌ HTTP client test failed: {e}")

def test_concurrent_requests():
    """Test concurrent request handling"""
    print("\n⚡ Testing Concurrent Requests...")
    
    client = get_http_client()
    
    try:
        import concurrent.futures
        import time
        
        start_time = time.time()
        
        # Submit multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            # Test multiple file requests
            test_files = ["alpha.txt", "beta.txt", "gamma.txt", "delta.txt", "epsilon.txt"]
            
            for file_name in test_files:
                future = executor.submit(client.fetch_file_from_node, "127.0.0.1:8080", file_name)
                futures.append((future, file_name))
            
            # Collect results
            results = []
            for future, file_name in futures:
                try:
                    success, data = future.result(timeout=10)
                    results.append({
                        'file_name': file_name,
                        'success': success,
                        'exists': data.get('exists', False) if data else False
                    })
                except Exception as e:
                    results.append({
                        'file_name': file_name,
                        'success': False,
                        'error': str(e)
                    })
        
        elapsed = time.time() - start_time
        successful = len([r for r in results if r['success']])
        
        print(f"✅ Concurrent requests completed in {elapsed:.2f}s")
        print(f"   Successful: {successful}/{len(results)}")
        
        for result in results:
            status = "✅" if result['success'] else "❌"
            file_status = "exists" if result.get('exists') else "not found"
            print(f"   {status} {result['file_name']}: {file_status}")
        
    except Exception as e:
        print(f"❌ Concurrent requests test failed: {e}")

def test_error_handling():
    """Test error handling and resilience"""
    print("\n🛡️ Testing Error Handling...")
    
    client = get_http_client()
    request_maker = get_request_maker()
    
    try:
        # Test connection to non-existent server
        success, data = client.fetch_file_from_node("127.0.0.1:9999", "test.txt")
        print(f"✅ Non-existent server test: success={success} (expected False)")
        
        # Test invalid URL
        try:
            request = HTTPRequest(method="GET", url="invalid-url")
            response = request_maker.make_request(request)
            print(f"❌ Invalid URL should have failed")
        except Exception as e:
            print(f"✅ Invalid URL properly handled: {type(e).__name__}")
        
        # Test timeout
        try:
            request = HTTPRequest(
                method="GET", 
                url="http://httpbin.org/delay/10",  # 10 second delay
                timeout=(1, 2)  # 1 second connect, 2 second read timeout
            )
            response = request_maker.make_request(request)
            print(f"❌ Timeout should have occurred")
        except Exception as e:
            print(f"✅ Timeout properly handled: {type(e).__name__}")
        
        print("✅ Error handling tests completed")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")

def main():
    """Run all HTTP component tests"""
    print("🚀 Starting HTTP Components Test Suite")
    print("=" * 50)
    
    try:
        # Run all tests
        test_connection_pool()
        test_request_maker()
        test_http_client()
        test_concurrent_requests()
        test_error_handling()
        
        print("\n" + "=" * 50)
        print("🎉 All HTTP component tests completed!")
        print("\n💡 Tips:")
        print("   - Check Prometheus metrics at http://127.0.0.1:8080/metrics")
        print("   - Monitor logs for detailed request information")
        print("   - Use the HTTP client in your application for inter-node communication")
        
    except KeyboardInterrupt:
        print("\n⛔ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        shutdown_http_client()
        print("✅ Cleanup completed")

if __name__ == "__main__":
    # Check if server is running
    print("📋 Pre-flight check: Ensure the main application is running")
    print("   Run: python main.py")
    print("   Server should be available at http://127.0.0.1:8080")
    
    input("\n⏳ Press Enter to continue when server is ready...")
    
    main()
