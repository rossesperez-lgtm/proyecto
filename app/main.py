from fastapi import FastAPI

from app.api import auth, users

app = FastAPI(title="Authentication and Authorization API", version="0.1.0")
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Return the API health status."""
    return {"status": "ok"}
