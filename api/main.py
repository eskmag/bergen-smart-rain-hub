import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import config, observations, simulate, costs, treatment, bydel

app = FastAPI(title="Bergen Smart Rain Hub API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router, prefix="/api")
app.include_router(observations.router, prefix="/api")
app.include_router(simulate.router, prefix="/api")
app.include_router(costs.router, prefix="/api")
app.include_router(treatment.router, prefix="/api")
app.include_router(bydel.router, prefix="/api")
