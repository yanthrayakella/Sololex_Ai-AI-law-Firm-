import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.orchestration import run_all_agents
from config import settings
from db import init_db
from routers import alerts, auth, contracts, dashboard, demo_judge, user, webhook
from seed import seed_if_empty

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("complyai")

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_if_empty()
    scheduler.add_job(
        run_all_agents,
        "interval",
        hours=settings.scraper_interval_hours,
        id="complyai_agents",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: agents every %s hours", settings.scraper_interval_hours)
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="ComplyAI — Contract Intelligence", lifespan=lifespan)
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(demo_judge.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(contracts.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)
app.include_router(webhook.router)


@app.get("/health")
def health():
    return {"status": "ok"}
