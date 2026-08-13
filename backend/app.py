# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router using the package path
from backend.routes.api import router
from backend.routes.auth_routes import router as auth_router

app = FastAPI(title="Study Agent API")

# CORS setup (allows frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Register routes
app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
