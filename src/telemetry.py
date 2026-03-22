"""OpenTelemetry: OTLP gRPC → Jaeger; связка с Traefik по W3C traceparent.

Отключить экспорт: OTEL_SDK_DISABLED=true
Локально без Docker: OTEL_SDK_DISABLED=true или OTEL_EXPORTER_OTLP_ENDPOINT=
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_fastapi_tracing(app: FastAPI, default_service_name: str) -> None:
    if os.getenv("OTEL_SDK_DISABLED", "").lower() in ("1", "true", "yes"):
        return
    raw = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if raw is not None and not str(raw).strip():
        return
    endpoint = (raw or "jaeger:4317").strip()
    service_name = (os.getenv("OTEL_SERVICE_NAME") or default_service_name).strip() or default_service_name

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor().instrument_app(app)
    logger.info("OpenTelemetry tracing enabled (service=%s, endpoint=%s)", service_name, endpoint)

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX client instrumentation enabled")
    except ImportError:
        pass
