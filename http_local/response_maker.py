
# HTTP response maker logic
from flask import jsonify, make_response

def make_http_response(data, status=200, headers=None):
    resp = make_response(jsonify(data), status)
    # Add standard headers
    standard_headers = {
        'X-Server': 'DistributedSearch',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
        'Access-Control-Allow-Origin': '*',
        'X-Request-Processed': 'true'
    }
    for k, v in standard_headers.items():
        resp.headers[k] = v
    if headers:
        for k, v in headers.items():
            resp.headers[k] = v
    return resp
