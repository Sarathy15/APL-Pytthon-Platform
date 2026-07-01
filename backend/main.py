from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api.routes import upload, convert, validate, report, scores, health, compare, understand, tests
from .api.middleware.logging import LoggingMiddleware
from .api.middleware.exception_handler import ExceptionHandlerMiddleware

app = FastAPI(title="APL Migration Platform - Enterprise Backend")

# Middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router, prefix="/api/health", tags=["System"])
app.include_router(upload.router, prefix="/api/upload", tags=["Ingestion"])
app.include_router(understand.router, prefix="/api/understand", tags=["Agents"])
app.include_router(convert.router, prefix="/api/convert", tags=["Agents"])
app.include_router(tests.router, prefix="/api/tests", tags=["Agents"])
app.include_router(validate.router, prefix="/api/validate", tags=["Validation"])
app.include_router(scores.router, prefix="/api/scores", tags=["Metrics"])
app.include_router(report.router, prefix="/api/report", tags=["Reporting"])
app.include_router(compare.router, prefix="/api/compare", tags=["Analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
