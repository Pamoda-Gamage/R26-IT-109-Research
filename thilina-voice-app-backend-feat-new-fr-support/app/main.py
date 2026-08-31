from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.logger import logger
from app.database import init_db
from app.routers import chats, websocket


app = FastAPI(title="Dispatch Chat API")


logger.info("[cyan]Initializing Dispatch Chat API...[/cyan]")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("[green]CORS middleware configured[/green]")


app.mount("/media", StaticFiles(directory="media"), name="media")

logger.info("[green]Static media route mounted[/green]")


app.include_router(chats.router)
logger.info("[green]Chat router registered[/green]")


app.include_router(websocket.router)
logger.info("[green]WebSocket router registered[/green]")


@app.on_event("startup")
def on_startup():
    logger.info("[yellow]Starting dispatch NLP services...[/yellow]")

    try:
        init_db()
        logger.info("[green]Database initialized successfully[/green]")

    except Exception:
        logger.exception("[bold red]Database initialization failed[/bold red]")
        raise

    logger.info(
        "[bold green]Dispatch Voice Service Backend Started Successfully[/bold green]"
    )