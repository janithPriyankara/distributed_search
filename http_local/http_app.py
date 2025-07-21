

# HTTP server logic
# This file should be renamed to http_app.py to avoid shadowing Python's stdlib http.server



from flask import Flask, request
from http_local.controller import handle_get_file, handle_get_all_files, handle_add_file
from http_local.response_maker import make_http_response



app = Flask(__name__)

@app.route('/file/<file_name>', methods=['GET'])
def get_file(file_name):
    data, status = handle_get_file(file_name)
    return make_http_response(data, status)

@app.route('/files', methods=['GET'])
def get_all_files():
    data, status = handle_get_all_files()
    return make_http_response(data, status)

@app.route('/file', methods=['POST'])
def add_file():
    req = request.get_json()
    file_name = req.get('file_name') if req else None
    data, status = handle_add_file(file_name)
    return make_http_response(data, status)

from common.property_loader import get_property

def run_http_server():
    host = get_property('service_host', '0.0.0.0')
    port = get_property('service_port', 8080)
    print(f"Starting {get_property('service_name')} on {host}:{port}")
    print(f"Bootstrap server: {get_property('bootstrap_server_addr')}")
    print(f"Additional data: {get_property('additional_data')}")
    app.run(host=host, port=port)
