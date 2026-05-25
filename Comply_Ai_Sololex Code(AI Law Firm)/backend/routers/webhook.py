from fastapi import APIRouter

from agents.orchestration import run_all_agents

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


@router.post("/scrape")
def trigger_scrape():
    run_all_agents()
    return {"status": "ok", "message": "Scraper and analysis agents executed"}
