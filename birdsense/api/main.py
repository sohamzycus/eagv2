"""
🐦 BirdSense REST API Server
Developed by Soham

FastAPI-based REST API for bird identification.
Run: uvicorn api.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from datetime import datetime

# Import routes
from api.routes import auth_router, identify_router

# Import for health check
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import BIRDNET_AVAILABLE
from providers import provider_factory
from api.models import HealthResponse


# ============ CREATE APP ============

app = FastAPI(
    title="🐦 BirdSense API",
    description="""
## Bird Identification REST API

**Developed by Soham**

BirdSense provides AI-powered bird identification through:
- **Audio Analysis**: BirdNET + LLM hybrid with multi-bird detection
- **Image Analysis**: Vision AI with feature-based identification
- **Description Matching**: Natural language bird identification

### Authentication
All identification endpoints require JWT authentication.
Use `/auth/login` to get a token.

### Default Users
| Username | Password | Role |
|----------|----------|------|
| `mazycus` | `ZycusMerlinAssist@2024` | Admin |
| `demo` | `demo123` | Demo |
| `soham` | `birdsense2024` | Developer |
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ============ CORS ============

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ ROUTES ============

app.include_router(auth_router)
app.include_router(identify_router)


# ============ ROOT ENDPOINTS ============

@app.get("/", tags=["Status"])
async def root():
    """API root - basic info."""
    return {
        "name": "BirdSense API",
        "version": "1.0.0",
        "developer": "Soham",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Status"])
async def health_check():
    """Health check endpoint."""
    active = provider_factory.get_active()
    if active:
        status = active.get_status()
        llm_backend = status.name
        llm_status = "connected" if status.available else f"error: {status.error}"
    else:
        llm_backend = "None"
        llm_status = "not configured"
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        birdnet_available=BIRDNET_AVAILABLE,
        llm_backend=llm_backend,
        llm_status=llm_status,
        timestamp=datetime.utcnow()
    )


# ============ CUSTOM OPENAPI ============

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="🐦 BirdSense API",
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token from /auth/login"
        }
    }
    
    # Apply security to all paths except auth
    for path in openapi_schema["paths"]:
        if not path.startswith("/auth") and path not in ["/", "/health"]:
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ============ MAIN ============

if __name__ == "__main__":
    import uvicorn
    print("🐦 BirdSense API Server")
    print("=" * 50)
    print("Developed by Soham")
    print("=" * 50)
    print(f"BirdNET: {'✅' if BIRDNET_AVAILABLE else '❌'}")
    print("=" * 50)
    print("Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

