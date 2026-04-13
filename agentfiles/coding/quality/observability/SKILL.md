---
name: observability
description: >
  Use when adding structured logging, distributed tracing (OpenTelemetry),
  metrics instrumentation, or alerting to an application. Covers the three
  pillars of observability: logs, traces, and metrics. Not for print debugging.
  Low-priority — invoke when observability is the stated task.
---

# Observability

Structured logging, distributed tracing, and metrics instrumentation.
Makes production systems debuggable without SSH access.

**Core principle:** You cannot fix what you cannot see. Observability is
not about collecting data — it's about answering questions you haven't
thought of yet.

## When to Use

- Adding logging to a new service or feature
- Instrumenting an application with OpenTelemetry tracing
- Setting up metrics (counters, histograms, gauges)
- Designing alerting rules for production systems
- Replacing print-statement debugging with structured logging
- Debugging production issues that can't be reproduced locally
- Setting up log aggregation (ELK, Loki, CloudWatch)

## When NOT to Use

- **Debugging locally** — use `systematic-debugging` with breakpoints
- **Performance profiling** — use `performance-profiling` for CPU/memory analysis
- **Infrastructure monitoring** (uptime, disk, CPU) — use `infrastructure-expert`
- **Security audit logging** — use `security-review` for compliance requirements

## The Iron Law

```
LOG THE CONTEXT, NOT THE DATA
```

Log what happened, when, where, and why — not the raw payload.
Sensitive data in logs becomes a liability, not an asset.

## The Three Pillars

### 1. Structured Logging

**Every log entry must be structured (JSON), not a formatted string.**

```python
# BAD: unstructured, unsearchable
logger.info(f"User {user_id} placed order {order_id} for ${amount}")

# GOOD: structured, queryable
logger.info(
    "order_placed",
    extra={
        "user_id": user_id,
        "order_id": order_id,
        "amount": amount,
        "currency": "USD",
    },
)
```

**Log levels — use them consistently:**

| Level | When to Use |
|-------|-------------|
| `ERROR` | Something failed and needs human attention |
| `WARNING` | Something unexpected but handled (retries, fallbacks) |
| `INFO` | Business-significant events (order placed, user signed up) |
| `DEBUG` | Development-time detail, disabled in production |

**What to log at each request boundary:**
- Request received: method, path, request ID
- Request completed: status code, duration, request ID
- External call made: service, endpoint, duration, success/failure

**Correlation IDs:** Every request gets a unique ID. Pass it through every
service call. Include it in every log entry. This is what ties logs together
across services.

### 2. Distributed Tracing (OpenTelemetry)

Tracing shows the path a request takes through your system.

```python
# OpenTelemetry setup (Python)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# Instrument a function
with tracer.start_as_current_span("process_order") as span:
    span.set_attribute("order.id", order_id)
    span.set_attribute("order.items", len(items))
    result = process(order)
    span.set_attribute("order.total", result.total)
```

**Tracing rules:**
- Instrument at service boundaries (HTTP, gRPC, message queue)
- Add custom spans for significant internal operations
- Attach business-relevant attributes to spans
- Propagate trace context across service calls (W3C Trace Context headers)
- Sample in production — 100% tracing is expensive at scale

### 3. Metrics

Metrics answer "how much" and "how fast" — aggregated, not per-request.

**The four golden signals (from Google SRE):**

| Signal | Metric Type | Example |
|--------|-------------|---------|
| **Latency** | Histogram | Request duration (p50, p95, p99) |
| **Traffic** | Counter | Requests per second |
| **Errors** | Counter | 5xx responses per second |
| **Saturation** | Gauge | CPU usage, memory usage, queue depth |

```python
# Prometheus metrics (Python)
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)
```

## Alerting Patterns

**Alert on symptoms, not causes:**
- Alert: "Error rate > 5% for 5 minutes" (symptom)
- Don't alert: "Pod restarted" (cause — may self-heal)

**Every alert must have:**
1. A clear description of what's wrong
2. A runbook link explaining what to do
3. An owner who will respond

**Alert fatigue kills observability.** If alerts fire often and get ignored,
the system has no observability. Tune thresholds, fix noisy alerts, or delete them.

## Anti-patterns

| Anti-pattern | Why It's Bad | Instead |
|-------------|-------------|---------|
| `print()` in production | Unstructured, no levels, no context | Structured logging with proper library |
| Logging PII or secrets | Compliance violation, security risk | Redact sensitive fields |
| Logging everything at INFO | Noise drowns signal, storage costs | INFO for business events, DEBUG for detail |
| No correlation ID | Can't trace a request across logs | Generate and propagate request IDs |
| Metrics with unbounded cardinality | Explodes storage, crashes dashboards | Limit label values (no user IDs in labels) |
| Alerting on every error | Alert fatigue → alerts get ignored | Alert on error rate thresholds |
| No sampling in tracing | Huge cost at scale | Sample 1-10% in production |
| Logging inside tight loops | Performance degradation, log flood | Log at boundaries, not per-iteration |

## Tools

| Tool | Purpose | Setup |
|------|---------|-------|
| OpenTelemetry | Tracing and metrics standard | SDK per language |
| Prometheus | Metrics collection and alerting | `prometheus.yml` config |
| Grafana | Dashboards and visualization | Connect to Prometheus/Loki |
| Loki | Log aggregation (Grafana ecosystem) | Lightweight, label-based |
| Jaeger / Tempo | Trace storage and visualization | OTLP-compatible backends |
| structlog (Python) | Structured logging library | `pip install structlog` |
| pino (Node.js) | Fast structured JSON logging | `npm install pino` |
| tracing (Rust) | Structured logging + spans | `cargo add tracing` |

## Outputs

- Structured logging configuration with consistent levels and correlation IDs
- OpenTelemetry instrumentation for critical paths
- Metrics definitions covering the four golden signals
- Alerting rules with thresholds, descriptions, and runbook links
- Chain into `verification-before-completion` to confirm instrumentation works
