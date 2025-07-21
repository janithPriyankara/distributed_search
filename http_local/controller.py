
# HTTP controller logic
import os
import random
import base64
from common.file_memory import FileMemory
from common.file_generator import generate_file

file_memory = FileMemory()

def handle_get_file(file_name):
    if file_memory.has_file(file_name):
        response = {'file': file_name}
        size_mb = random.randint(1, 5)
        content = os.urandom(size_mb * 1024 * 1024)
        file_path = f"/tmp/{file_name}"
        generate_file(file_path, content)
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        response['file_data'] = encoded
        response['file_size_mb'] = size_mb
        return response, 200
    else:
        return {'error': 'File not found', 'file': file_name}, 404

def handle_get_all_files():
    return {'files': file_memory.list_files()}, 200

def handle_add_file(file_name):
    if not file_name:
        return {'error': 'file_name required'}, 400
    if file_memory.has_file(file_name):
        return {'error': 'File already exists', 'file': file_name}, 409
    file_memory.add_file(file_name)
    return {'added': file_name}, 201
