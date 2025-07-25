

# HTTP server logic
# This file should be renamed to http_app.py to avoid shadowing Python's stdlib http.server



from flask import Flask, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from http_local.controller import handle_get_file, handle_get_all_files, handle_add_file
from http_local.response_maker import make_http_response



app = Flask(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'HTTP request latency', ['endpoint'])

# OpenTelemetry tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name='localhost',
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
FlaskInstrumentor().instrument_app(app)

@app.route('/file/<file_name>', methods=['GET'])
def get_file(file_name):
    import time
    start = time.time()
    data, status = handle_get_file(file_name)
    REQUEST_COUNT.labels(method='GET', endpoint='/file/<file_name>', http_status=status).inc()
    REQUEST_LATENCY.labels(endpoint='/file/<file_name>').observe(time.time() - start)
    return make_http_response(data, status)

@app.route('/files', methods=['GET'])
def get_all_files():
    import time
    start = time.time()
    data, status = handle_get_all_files()
    REQUEST_COUNT.labels(method='GET', endpoint='/files', http_status=status).inc()
    REQUEST_LATENCY.labels(endpoint='/files').observe(time.time() - start)
    return make_http_response(data, status)

@app.route('/file', methods=['POST'])
def add_file():
    import time
    start = time.time()
    req = request.get_json()
    file_name = req.get('file_name') if req else None
    data, status = handle_add_file(file_name)
    REQUEST_COUNT.labels(method='POST', endpoint='/file', http_status=status).inc()
    REQUEST_LATENCY.labels(endpoint='/file').observe(time.time() - start)
    return make_http_response(data, status)
@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health():
    """Health check endpoint"""
    import time
    return {
        'status': 'healthy',
        'timestamp': time.time(),
        'service': get_property('service_name', 'http_service'),
        'version': '1.0.0'
    }, 200

from common.property_loader import get_property

def run_http_server():
    host = get_property('service_host', '0.0.0.0')
    port = get_property('service_port', 8080)
    print(f"Starting {get_property('service_name')} on {host}:{port}")
    print(f"Bootstrap server: {get_property('bootstrap_server_addr')}")
    print(f"Additional data: {get_property('additional_data')}")
    app.run(host=host, port=port)
