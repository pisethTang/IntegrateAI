from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os 
import logging

import time
from datetime import datetime

import json
import random

from contextlib import asynccontextmanager



from sqlalchemy import func
from sqlalchemy.orm import Session
from models import SessionLocal, get_db, Integration, SyncLog, SyncHash, engine, Base
from fastapi import Depends



from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _build_allowed_origins() -> list[str]:
    origins = {"http://localhost:3000"}
    configured_origins = os.getenv("FRONTEND_URL", "")

    for origin in configured_origins.split(","):
        normalized_origin = origin.strip().rstrip("/")
        if normalized_origin:
            origins.add(normalized_origin)

    return sorted(origins)


# Import the sync engine
from sync_engine import SyncEngine


# Import the RL optimizer
from rl_optimizer import SyncOptimizer


# Initialize RL optimizer
rl_optimizer = SyncOptimizer()



from ai_agent import IntegrationAI


# Initialize AI agent
ai_agent = IntegrationAI()










# Set up logging
logging.basicConfig(level=logging.INFO)

def get_db_session():
    return SessionLocal()




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    Base.metadata.create_all(bind=engine)
    
    # Seed default integration
    db = SessionLocal()
    existing = db.query(Integration).filter(Integration.id == "1").first()
    if not existing:
        default = Integration(
            id="1",
            name="Google Sheets → Airtable",
            source_type="google_sheets",
            source_config={
                "api_key": os.getenv("GOOGLE_SHEETS_API_KEY"),
                "sheet_id": "1mvOI4i6ekfQv5nBzKAropDMTQ1jUCAEKwiLM_JrjNxc",
                "range": "Sheet1"
            },
            target_type="airtable",
            target_config={
                "api_key": os.getenv("AIRTABLE_API_KEY"),
                "base_id": "appD0lElNLFW3IMTu",
                "table": "Projects"
            },
            field_mapping={"Name": "Name", "Status": "Status", "Due Date": "Deadline"}
        )
        db.add(default)
        db.commit()
    db.close()
    
    yield  # App runs here
    
    # Shutdown code (oPtional)
    print("Shutting down...")


app = FastAPI(title="IntegrateAI API", lifespan=lifespan) # lifespan allows us to run startup code before the app starts accepting requests

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import types Request/Response models
# from backend.types.ChatRequest import ChatRequest
# from backend.types.ChatResponse import ChatResponse
# from backend.types.Action import Action

class Action(BaseModel):
    label: str
    action: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    actions: Optional[List[Action]] = None


class IntegrationSummary(BaseModel):
    id: str
    name: str
    status: str
    source: str
    target: str
    last_sync: Optional[str] = None
    next_sync: Optional[str] = None
    sync_count: int = 0





@app.get("/")
def root():
    return {"message": "IntegrateAI API is running"}




@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """AI chat endpoint with Gemini"""
    try:
        result = ai_agent.chat(request.message)
    except Exception as e:
        logging.exception("/chat failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Chat provider error: {str(e)}")
    
    return ChatResponse(
        response=result["response"],
        actions=[Action(label=a["label"], action=a["action"]) for a in result.get("actions", [])]
    )



@app.get("/integrations", response_model=List[IntegrationSummary])
def get_integrations(db: Session = Depends(get_db)) -> list[IntegrationSummary]:
    """Get all integrations"""
    try:
        integrations = db.query(Integration).all()
        if not integrations:
            logging.info("No integrations found")
            return []

        integration_ids = [integration.id for integration in integrations]
        sync_stats = (
            db.query(
                SyncLog.integration_id,
                func.count(SyncLog.id).label("sync_count"),
                func.max(SyncLog.timestamp).label("last_sync"),
            )
            .filter(SyncLog.integration_id.in_(integration_ids))
            .group_by(SyncLog.integration_id)
            .all()
        )

        stats_by_integration_id = {
            row.integration_id: {
                "sync_count": int(row.sync_count),
                "last_sync": row.last_sync.isoformat() if row.last_sync else None,
            }
            for row in sync_stats
        }

        payload: List[IntegrationSummary] = []
        for integration in integrations:
            stats = stats_by_integration_id.get(
                integration.id, {"sync_count": 0, "last_sync": None}
            )
            payload.append(
                IntegrationSummary(
                    id=integration.id,
                    name=integration.name,
                    status=integration.status or "unknown",
                    source=integration.source_type or "unknown",
                    target=integration.target_type or "unknown",
                    last_sync=stats["last_sync"],
                    next_sync=None,
                    sync_count=stats["sync_count"],
                )
            )

        logging.info("Fetched %s integrations", len(payload))
        return payload
    except Exception as e:
        logging.exception("Failed to fetch integrations: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch integrations")



METRICS_FILE: str = "sync_metrics.json"

def load_metrics():
    """Load metrics from file on startup"""
    global sync_metrics
    try:
        with open(METRICS_FILE, "r") as f:
            sync_metrics = json.load(f)
    except FileNotFoundError:
        sync_metrics = []

def save_metrics() -> bool:
    """Save metrics to file"""
    try:
        with open(METRICS_FILE, "w") as f:
            json.dump(sync_metrics, f)
            return True
    except Exception as e:
        logging.exception("Failed to save metrics: %s", e)
        return False

# Load on startup
load_metrics()


###############################################################
# Store last sync hashes (persist to file)
sync_hashes = {}

def load_hashes():
    global sync_hashes
    try:
        with open("sync_hashes.json", "r") as f:
            sync_hashes = json.load(f)
    except FileNotFoundError:
        sync_hashes = {}

def save_hashes():
    with open("sync_hashes.json", "w") as f:
        json.dump(sync_hashes, f)

# Load on startup
load_hashes()

###############################################################



@app.post("/sync/{integration_id}/trigger")
def trigger_sync(integration_id: str, db: Session = Depends(get_db)):
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        return {"status": "error", "message": "Integration not found"}
    
    start_time = time.time()
    
    try:
        # Build source config with type from model
        source_config = integration.source_config.copy()
        source_config["type"] = integration.source_type  # <-- USE THIS!
        
        # Build target config with type from model
        target_config = integration.target_config.copy()
        target_config["type"] = integration.target_type  # <-- USE THIS!
        
        engine_sync = SyncEngine(source_config, target_config, integration.field_mapping)
        
        # Check hash
        hash_record = db.query(SyncHash).filter(SyncHash.integration_id == integration_id).first()
        if hash_record:
            engine_sync.last_sync_hash = hash_record.last_hash
        
        result = engine_sync.sync(
            integration.source_config["sheet_id"],
            integration.target_config["table"],
            integration.source_config.get("range", "Sheet1")
        )
        
        # Save hash
        if result.get("status") == "success":
            if hash_record:
                hash_record.last_hash = engine_sync.last_sync_hash
                hash_record.updated_at = datetime.utcnow()
            else:
                db.add(SyncHash(
                    integration_id=integration_id,
                    last_hash=engine_sync.last_sync_hash
                ))
        
        # Log sync
        db.add(SyncLog(
            integration_id=integration_id,
            duration_ms=(time.time() - start_time) * 1000,
            rows_read=result.get("rows_read", 0),
            rows_written=result.get("rows_written", 0),
            api_calls=2,
            status=result.get("status", "unknown")
        ))
        db.commit()
        
        return result
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}









@app.get("/metrics/sync-history")
def get_sync_history(db: Session = Depends(get_db)):
    logs = db.query(SyncLog).order_by(SyncLog.timestamp.desc()).limit(50).all()
    return {
        "total_syncs": db.query(SyncLog).count(),
        "metrics": [
            {
                "timestamp": log.timestamp.isoformat() if log.timestamp else None, 
                "integration_id": log.integration_id, 
                "rows_written": log.rows_written, 
                "status": log.status
            } 
            
            for log in logs
            ]
    }

@app.get("/metrics/efficiency")
def get_efficiency(db: Session = Depends(get_db)):
    total = db.query(SyncLog).count()
    if total == 0:
        return {"total_syncs": 0, "wasted_syncs": 0, "efficiency": 0}
    
    wasted = db.query(SyncLog).filter(SyncLog.rows_written == 0).count()
    return {
        "total_syncs": total,
        "wasted_syncs": wasted,
        "efficiency": ((total - wasted) / total * 100)
    }



# Fixed scheule endpoint (for demo purposes)
@app.post("/test/fixed-schedule")
def test_fixed_schedule(hours: int = 168): # 168 hrs = 1 week
    """Test sync efficiency with fixed 30-minute schedule"""
    
    sync_count = 0
    useful_syncs = 0
    wasted_syncs = 0
    
    # Simulate checking every 30 minutes
    # Simulation ALWAYS starts at Monday midnight (12:00 AM).
    # example: 
    # hour = 3 then we'll consider 
    # Monday 0:00 - 0:30 (hour=0, minute=0)
    # Monday 0:30 - 1:00 (hour=0, minute=30)
    # Monday 1:00 - 1:30 (hour=1, minute=0)
    # Monday 1:30 - 2:00 (hour=1, minute=30)
    # Monday 2:00 - 2:30 (hour=2, minute=0)
    # Monday 2:30 - 3:00 (hour=2, minute=30)
    for hour in range(hours):
        for minute in [0, 30]:  # Check at :00 and :30
            sync_count += 1
            
            # Check if data changed (use simulator logic)
            change_prob = get_change_probability(hour, minute)
            data_changed = random.random() < change_prob
            
            if data_changed:
                useful_syncs += 1
            else:
                wasted_syncs += 1
    
    return {
        "strategy": "Fixed (every 30 min)",
        "total_syncs": sync_count,
        "useful_syncs": useful_syncs,
        "wasted_syncs": wasted_syncs,
        "efficiency": (useful_syncs / sync_count * 100) if sync_count > 0 else 0,
        "api_calls": sync_count * 2  # Read + write attempt
    }

def get_change_probability(hour: int, minute: int) -> float:
    """Helper to determine if data changed at given time"""
    day = (hour // 24) % 7
    hour_of_day = hour % 24
    
    # Monday morning rush
    if day == 0 and 9 <= hour_of_day <= 11:
        return 0.8
    
    # Friday afternoon
    elif day == 4 and 16 <= hour_of_day <= 18:
        return 0.7
    
    # Business hours
    elif 9 <= hour_of_day <= 17 and day < 5:
        return 0.3
    
    # Weekends
    elif day >= 5:
        return 0.05
    
    # Off-hours ()
    else:
        return 0.1
# ####################################################################################



# rl optimizer endpoints
@app.post("/rl/train")
def train_rl_optimizer():
    """Train the RL sync optimizer"""
    given_total_timesteps = 20000
    result = rl_optimizer.train(total_timesteps=given_total_timesteps)
    return result





@app.get("/rl/status")
def get_rl_status():
    """Check if RL model is trained"""
    return {
        "is_trained": rl_optimizer.is_trained,
        "model_loaded": os.path.exists("rl_model.zip")
    }




@app.post("/rl/should-sync")
def should_sync_rl(hours_since_sync: int):
    """Ask RL agent if we should sync now"""
    state = {
        "hour_of_day": datetime.now().hour,
        "day_of_week": datetime.now().weekday(),
        "hours_since_sync": hours_since_sync,
        "api_calls_today": len(sync_metrics),  # Approximate
        "data_change_score": 50  # Default
    }
    
    should = rl_optimizer.should_sync(state)
    return {"should_sync": should, "state": state}

@app.get("/rl/evaluate")
def evaluate_rl():
    """Compare RL vs fixed schedule"""
    if not rl_optimizer.is_trained:
        # Try to load existing model
        if not rl_optimizer.load():
            return {"error": "No trained model. Train first with POST /rl/train"}
    
    return rl_optimizer.evaluate(episodes=10)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
