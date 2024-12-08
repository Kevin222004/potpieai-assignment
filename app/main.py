from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.endpoints import github
from app.db.session import init_db
from app.utils.rate_limiter import RateLimiter
from app.utils.logger import logger
import time

app = FastAPI(
    title="Code Review Agent",
    description="AI-powered code review system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiter
rate_limiter = RateLimiter()


# Middleware for logging and rate limiting
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # Rate limiting
    await rate_limiter.check_rate_limit(request)

    # Request timing
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Log request details
    logger.info(
        "Request processed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "process_time": process_time,
            "status_code": response.status_code
        }
    )

    response.headers["X-Process-Time"] = str(process_time)
    return response


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Global exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc)
        },
        exc_info=exc
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )


# Include routers
app.include_router(github.router, prefix="/api/v1", tags=["github"])


@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")
    await init_db()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}