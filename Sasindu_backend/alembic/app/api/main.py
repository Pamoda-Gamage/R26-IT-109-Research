from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, bandit_state, feedback, providers, request, simulate, ws_bandit

app = FastAPI(title="Provider Match API")

upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.add_middleware(
    CORSMiddleware,
    # Dev-only: Next.js runs on a host port that varies (3000, falls back to 3001, ...),
    # and the frontend calls the backend directly from the browser (no proxy in front).
    # "null" covers the research-panel demo HTML page when opened directly via file://
    # instead of served through Next.js.
    allow_origin_regex=r"http://localhost(:\d+)?",
    allow_origins=["null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(providers.router)
app.include_router(feedback.router)
app.include_router(bandit_state.router)
app.include_router(request.router)
app.include_router(simulate.router)
app.include_router(ws_bandit.router)
