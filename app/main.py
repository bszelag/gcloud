"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import time

from app.core.config import settings
from app.api.v1.endpoints import hello

# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    description="A FastAPI-based birthday API with TDD approach",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Middleware to collect metrics."""
    start_time = time.time()
    
    # Increment active requests
    ACTIVE_REQUESTS.labels(method=request.method, endpoint=request.url.path).inc()
    
    # Process request
    response = await call_next(request)
    
    # Decrement active requests
    ACTIVE_REQUESTS.labels(method=request.method, endpoint=request.url.path).dec()
    
    # Record request duration
    duration = time.time() - start_time
    REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(duration)
    
    # Record request count
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests',
    ['method', 'endpoint']
)

# Include API routers
app.include_router(hello.router, tags=["hello"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Birthday API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 