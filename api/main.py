import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.routers import (
    config, observations, simulate, costs, treatment, bydel, energy, validation, admin,
)

app = FastAPI(title="Bergen Smart Rain Hub API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router, prefix="/api")
app.include_router(observations.router, prefix="/api")
app.include_router(simulate.router, prefix="/api")
app.include_router(costs.router, prefix="/api")
app.include_router(treatment.router, prefix="/api")
app.include_router(bydel.router, prefix="/api")
app.include_router(energy.router, prefix="/api")
app.include_router(validation.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend-react" / "dist"

if FRONTEND_DIST.exists():
    # Registered after the /api routers, so those explicit routes still win;
    # this mount only catches whatever they don't (built assets, SPA routes).
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    @app.exception_handler(StarletteHTTPException)
    async def spa_fallback(request: Request, exc: StarletteHTTPException):
        # Unmatched /api/* paths stay JSON 404s; everything else (client-side
        # routes like /beregn) falls back to index.html so a hard refresh works.
        #
        # /assets/* is excluded deliberately: those names are content-hashed, so
        # a miss means the caller is holding a stale index.html that references
        # a bundle we no longer ship. Answering with index.html would hand the
        # browser HTML where it expects JavaScript and take down the whole app
        # with an opaque syntax error — a plain 404 fails honestly instead.
        if exc.status_code == 404 and not request.url.path.startswith(("/api", "/assets")):
            return FileResponse(FRONTEND_DIST / "index.html")
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.middleware("http")
    async def cache_control(request: Request, call_next):
        # Vite fingerprints everything under /assets/, so those are safe to keep
        # forever; index.html names them and must therefore always be revalidated,
        # otherwise a heuristically cached copy keeps pointing at dead bundles.
        response = await call_next(request)
        if request.url.path.startswith("/api"):
            return response
        if response.status_code == 200 and request.url.path.startswith("/assets/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif response.headers.get("content-type", "").startswith("text/html"):
            response.headers["Cache-Control"] = "no-cache"
        return response
