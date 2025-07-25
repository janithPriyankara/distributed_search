# UDP server logic
import socket
from prometheus_client import Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

def start_udp_server():
    # Prometheus metrics
    UDP_PACKET_COUNT = Counter('udp_packets_total', 'Total UDP packets received', ['source'])
    UDP_PACKET_LATENCY = Histogram('udp_packet_latency_seconds', 'UDP packet processing latency')

    # OpenTelemetry tracing
    trace.set_tracer_provider(TracerProvider())
    jaeger_exporter = JaegerExporter(
        agent_host_name='localhost',
        agent_port=6831,
    )
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    tracer = trace.get_tracer(__name__)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 9000))
    print('UDP server started on port 9000')
    while True:
        import time
        start = time.time()
        data, addr = sock.recvfrom(1024)
        with tracer.start_as_current_span("udp_packet_received"):
            UDP_PACKET_COUNT.labels(source=str(addr)).inc()
            # Simulate processing
            print(f'Received from {addr}: {data}')
            UDP_PACKET_LATENCY.observe(time.time() - start)
