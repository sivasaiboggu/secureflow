import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Prometheus telemetry definitions
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Duration of HTTP requests in seconds",
    ["method", "endpoint"]
)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs the HTTP details of every incoming request and response"""
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        url = request.url.path
        
        logger.info(f"Incoming Request: {method} {url}")
        
        try:
            response: Response = await call_next(request)
            duration = time.time() - start_time
            logger.info(f"Completed Request: {method} {url} | Status: {response.status_code} | Duration: {duration:.4f}s")
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed Request: {method} {url} | Exception: {str(e)} | Duration: {duration:.4f}s", exc_info=True)
            raise e

class MetricsMiddleware(BaseHTTPMiddleware):
    """Tracks HTTP request counts and durations for Prometheus scraping"""
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = request.url.path
        
        # Don't track metrics endpoint itself to avoid noise
        if endpoint == "/metrics":
            return await call_next(request)
            
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            status_code = str(response.status_code)
            
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status_code).inc()
            HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            
            return response
        except Exception as e:
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status="500").inc()
            raise e
