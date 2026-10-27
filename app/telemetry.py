import logging

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# The logs API moved between SDK versions, so support both locations.
try:
    from opentelemetry._logs import set_logger_provider
except ImportError:
    from opentelemetry.logs import set_logger_provider
try:
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import (
        ConsoleLogExporter,
        SimpleLogRecordProcessor,
    )
except ImportError:
    from opentelemetry.sdk.logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk.logs.export import (
        ConsoleLogExporter,
        SimpleLogRecordProcessor,
    )


def setup_telemetry():
    resource = Resource.create({"service.name": "order-tracker"})

    # Traces -> console
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    # Metrics -> console (printed every 5 seconds)
    reader = PeriodicExportingMetricReader(
        ConsoleMetricExporter(), export_interval_millis=5000
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    # Logs -> console (only loggers under "app")
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(SimpleLogRecordProcessor(ConsoleLogExporter()))
    set_logger_provider(logger_provider)
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))

    meter = metrics.get_meter("order-tracker")
    return meter.create_counter(
        "http_requests_total",
        unit="1",
        description="HTTP requests by route and status code",
    )