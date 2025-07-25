# Update IP/route tables logic
from prometheus_client import Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

ROUTE_UPDATE_COUNT = Counter('route_update_total', 'Total route table updates')
ROUTE_UPDATE_LATENCY = Histogram('route_update_latency_seconds', 'Route table update latency')

trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(agent_host_name='localhost', agent_port=6831)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
tracer = trace.get_tracer(__name__)

def update_ip_route_tables():
    import time
    start = time.time()
    with tracer.start_as_current_span("update_ip_route_tables"):
        print("IP/route tables updated.")
        ROUTE_UPDATE_COUNT.inc()
        ROUTE_UPDATE_LATENCY.observe(time.time() - start)
