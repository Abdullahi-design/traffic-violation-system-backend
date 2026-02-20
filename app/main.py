from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.routers import auth, users, violations, violation_types, payments, reports, notifications, dashboard
import os
import traceback

settings = get_settings()

app = FastAPI(
    title="Traffic Violation & Fine Management System",
    description="Backend API for managing traffic violations, fines, and payments",
    version="1.0.0",
    redirect_slashes=True,
)

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(violation_types.router)
app.include_router(violations.router)
app.include_router(payments.router)
app.include_router(reports.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


@app.get("/")
async def root():
    return {"message": "Traffic Violation & Fine Management System API", "docs": "/docs"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}
