# Request processing logic
from prometheus_client import Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

REQUEST_PROCESS_COUNT = Counter('request_process_total', 'Total requests processed')
REQUEST_PROCESS_LATENCY = Histogram('request_process_latency_seconds', 'Request processing latency')

trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(agent_host_name='localhost', agent_port=6831)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
tracer = trace.get_tracer(__name__)

def request_processing():
    import time
    start = time.time()
    with tracer.start_as_current_span("request_processing"):
        print("Processing requests.")
        REQUEST_PROCESS_COUNT.inc()
        REQUEST_PROCESS_LATENCY.observe(time.time() - start)
