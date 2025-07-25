
# HTTP controller logic
import os
import random
import base64
import logging
from common.file_memory import FileMemory
from common.file_generator import generate_file

logger = logging.getLogger(__name__)

file_memory = FileMemory()
# Add some default files for testing
default_files = ["alpha.txt", "beta.txt", "gamma.txt", "delta.txt", "epsilon.txt"]
for file_name in default_files:
    file_memory.add_file(file_name)

def handle_get_file(file_name):
    """
    Handle GET /file/<file_name> request
    
    Args:
        file_name: Name of the file to retrieve
        
    Returns:
        Tuple of (response_data, status_code)
    """
    try:
        if file_memory.has_file(file_name):
            # File exists locally - generate and return it
            response = {
                'file': file_name, 
                'exists': True,
                'source': 'local'
            }
            
            # Generate random file content (1MB-5MB)
            size_mb = random.randint(1, 5)
            content = os.urandom(size_mb * 1024 * 1024)
            
            # Use temp directory that works on Windows
            import tempfile
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, file_name)
            generate_file(file_path, content)
            
            # Encode file content as base64
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            
            response['file_data'] = encoded
            response['file_size_mb'] = size_mb
            
            logger.info(f"File '{file_name}' served from local storage ({size_mb}MB)")
            return response, 200
            
        else:
            # File not found locally - for now just return 404
            # Network search functionality can be added later to avoid circular imports
            logger.warning(f"File '{file_name}' not found locally")
            
            return {
                'file': file_name,
                'exists': False,
                'source': 'local_only',
                'message': 'File not found in local storage'
            }, 404
                
    except Exception as e:
        logger.error(f"Error handling get file '{file_name}': {e}")
        return {
            'error': 'Internal server error',
            'file': file_name,
            'exists': False
        }, 500

def handle_get_all_files():
    """
    Handle GET /files request
    
    Returns:
        Tuple of (response_data, status_code)
    """
    try:
        local_files = file_memory.list_files()
        
        response = {
            'files': local_files,
            'count': len(local_files),
            'source': 'local'
        }
        
        logger.info(f"Listed {len(local_files)} local files")
        return response, 200
        
    except Exception as e:
        logger.error(f"Error handling get all files: {e}")
        return {'error': 'Internal server error'}, 500

def handle_add_file(file_name):
    """
    Handle POST /file request
    
    Args:
        file_name: Name of the file to add
        
    Returns:
        Tuple of (response_data, status_code)
    """
    try:
        if not file_name:
            return {'error': 'file_name required'}, 400
            
        if file_memory.has_file(file_name):
            return {
                'error': 'File already exists', 
                'file': file_name
            }, 409
            
        file_memory.add_file(file_name)
        
        logger.info(f"File '{file_name}' added to local storage")
        
        return {
            'added': file_name,
            'message': 'File added successfully'
        }, 201
        
    except Exception as e:
        logger.error(f"Error handling add file '{file_name}': {e}")
        return {'error': 'Internal server error'}, 500
