# Main entry point for distributed search system

import threading
import time
import json
import logging
from node.registration import register_node
from node.update_tables import update_ip_route_tables
from common.file_memory import FileMemory
from http_local.http_app import run_http_server
from udp.server import start_udp_server
from node.request_processing import request_processing
from common.property_loader import load_properties, get_property

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    # Load service properties at startup
    load_properties("service_properties.json")
    print(f"Service name: {get_property('service_name')}")
    print(f"UDP server address: {get_property('udp_server_addr')}")
    register_node()
    update_ip_route_tables()
    file_memory = FileMemory()
    # Example: file_memory.add_file('example.txt')
    
    # Start UDP server in a separate thread
    udp_thread = threading.Thread(target=start_udp_server, daemon=True)
    udp_thread.start()
    
    # Start request processing in a separate thread
    request_thread = threading.Thread(target=request_processing, daemon=True)
    request_thread.start()
    
    # Start HTTP server (this will block, but now UDP server and request processing are already running)
    run_http_server()

if __name__ == "__main__":
    main()
