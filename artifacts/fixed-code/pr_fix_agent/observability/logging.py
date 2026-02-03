    if settings.log_format == "json":
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ]
from jsonpath_ng import parse
import structlog

# ... (rest of your code remains the same)

if settings.log_format == "json":
    processors = shared_processors + [
        structlog.processors.format_exc_info,
        # Use jsonpath-ng to sanitize sensitive fields
        parse('$.user_id').matches(lambda match: '**redacted**') >> 'redacted',
        structlog.processors.JSONRenderer(),
    ]
else:
    processors = shared_processors + [
        structlog.processors.format_exc_info,
        # Use python-json-logger to mask sensitive fields
        parse('$.user_id').matches(lambda match: '**redacted**') >> 'redacted',
        structlog.dev.ConsoleRenderer(),
    ]

structlog.configure(
    processors=processors,
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)