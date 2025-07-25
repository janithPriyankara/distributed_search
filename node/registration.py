# Node registration logic
from prometheus_client import Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

NODE_REGISTRATION_COUNT = Counter('node_registration_total', 'Total node registrations')
NODE_REGISTRATION_LATENCY = Histogram('node_registration_latency_seconds', 'Node registration latency')

trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(agent_host_name='localhost', agent_port=6831)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
tracer = trace.get_tracer(__name__)

def register_node():
    import time
    start = time.time()
    with tracer.start_as_current_span("register_node"):
        print("Node registered.")
        NODE_REGISTRATION_COUNT.inc()
        NODE_REGISTRATION_LATENCY.observe(time.time() - start)
