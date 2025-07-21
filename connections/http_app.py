

# HTTP server logic
# This file should be renamed to http_app.py to avoid shadowing Python's stdlib http.server

from flask import Flask, jsonify, request

import os
import random
from common.file_memory import FileMemory
from common.file_generator import generate_file


app = Flask(__name__)
file_memory = FileMemory()
# Add example file names to memory
for name in ["alpha.txt", "beta.txt", "gamma.txt", "delta.txt", "epsilon.txt"]:
    file_memory.add_file(name)

@app.route('/file/<file_name>', methods=['GET'])
def get_file(file_name):
    exists = file_memory.has_file(file_name)
    response = {'file': file_name, 'exists': exists}
    if exists:
        # Generate a random file (1MB-5MB)
        size_mb = random.randint(1, 5)
        content = os.urandom(size_mb * 1024 * 1024)
        file_path = f"/tmp/{file_name}"
        generate_file(file_path, content)
        # Attach file to response (send as base64 for JSON)
        import base64
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        response['file_data'] = encoded
        response['file_size_mb'] = size_mb
    return jsonify(response)

@app.route('/files', methods=['GET'])
def get_all_files():
    return jsonify({'files': file_memory.list_files()})

@app.route('/file', methods=['POST'])
def add_file():
    data = request.get_json()
    file_name = data.get('file_name')
    if file_name:
        file_memory.add_file(file_name)
        return jsonify({'added': file_name}), 201
    return jsonify({'error': 'file_name required'}), 400

def run_http_server():
    app.run(host='0.0.0.0', port=8080)
