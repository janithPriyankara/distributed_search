# Main entry point for distributed search system

from node.registration import register_node
from node.update_tables import update_ip_route_tables
from common.file_memory import FileMemory
from http_local.http_app import run_http_server
from udp.server import start_udp_server
from node.request_processing import request_processing
from common.property_loader import load_properties, get_property

def main():
    # Load service properties at startup
    load_properties("service_properties.json")
    print(f"Service name: {get_property('service_name')}")
    print(f"UDP server address: {get_property('udp_server_addr')}")
    register_node()
    update_ip_route_tables()
    file_memory = FileMemory()
    # Example: file_memory.add_file('example.txt')
    run_http_server()
    start_udp_server()
    request_processing()

if __name__ == "__main__":
    main()
