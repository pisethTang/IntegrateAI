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


from sqlalchemy.orm import Session
from models import get_db, Integration, SyncLog, SyncHash, engine, Base
from fastapi import Depends



from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))



# Import the sync engine
from sync_engine import SyncEngine



# Import the RL optimizer
from rl_optimizer import SyncOptimizer


# Initialize RL optimizer
rl_optimizer = SyncOptimizer()



from ai_agent import IntegrationAI


# Initialize AI agent
ai_agent = IntegrationAI()


#######################################################################################


# Store sync metrics (in production, use database)
sync_metrics = []






app = FastAPI(title="IntegrateAI API")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str

class Action(BaseModel):
    label: str
    action: str

class ChatResponse(BaseModel):
    response: str
    actions: Optional[List[Action]] = None

# THIS IS integration_configs - it stores the REAL connection details
# https://docs.google.com/spreadsheets/d/1mvOI4i6ekfQv5nBzKAropDMTQ1jUCAEKwiLM_JrjNxc/edit?usp=sharing
integration_configs = {
    "1": {
        "name": "Google Sheets → Airtable",
        "source": {
            "type": "google_sheets",
            "api_key": os.getenv("GOOGLE_SHEETS_API_KEY"),
            "sheet_id": "1mvOI4i6ekfQv5nBzKAropDMTQ1jUCAEKwiLM_JrjNxc",  # Replace with your actual sheet ID
            "range": "Sheet1"
        },
        "target": {
            "type": "airtable",
            "api_key": os.getenv("AIRTABLE_API_KEY"),
            "base_id": "appD0lElNLFW3IMTu",  # Replace with your actual base ID
            "table": "Projects"
        },
        "field_mapping": {
            "Name": "Name",
            "Status": "Status",
            "Due Date": "Deadline"
        }
    }
}

# This is for the dashboard display (can be fetched from DB later)
integrations_db = [
    {
        "id": "1",
        "name": "Google Sheets → Airtable",
        "source": "Projects",
        "target": "Active Projects",
        "status": "active",
        "lastSync": "2 min ago",
        "nextSync": "58 min",
        "syncCount": 128,
    },
]

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



@app.get("/integrations")
def get_integrations():
    """Get all integrations"""
    return integrations_db



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
def trigger_sync(integration_id: str):
    config = integration_configs.get(integration_id)
    if not config:
        return {"status": "error", "message": "Integration not found"}
    # print out the config for debugging
    logging.info(f"Triggering sync for integration {integration_id}: {config}")
    
    start_time = time.time()
    
    try:
        engine = SyncEngine(config["source"], config["target"], config["field_mapping"])
        
        # restore last hash if exists 
        if integration_id in sync_hashes:
            engine.last_sync_hash = sync_hashes[integration_id]

        result = engine.sync(
            config["source"]["sheet_id"],
            config["target"]["table"],
            config["source"].get("range", "Sheet1")
        )

        # save hash if sync was successful
        if result.get("status") == "success":
            sync_hashes[integration_id] = engine.last_sync_hash
            save_hashes()
        
        # Log metrics
        sync_metrics.append({
            "timestamp": datetime.now().isoformat(),
            "integration_id": integration_id,
            "duration_ms": (time.time() - start_time) * 1000,
            "rows_read": result.get("rows_read", 0),
            "rows_written": result.get("rows_written", 0),
            "api_calls": 2,
            "hour_of_day": datetime.now().hour
        })
        
        # Save to file
        success_flag: bool = save_metrics()
        if not success_flag:
            logging.error("Failed to save metrics after sync. Check the logs for details.")
        else:    
            logging.info("Metrics saved successfully after sync.")
        
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}



@app.get("/metrics/sync-history")
def get_sync_history():
    """Get sync metrics for visualization"""
    return {
        "total_syncs": len(sync_metrics),
        "metrics": sync_metrics[-50:]  # Last 50 syncs
    }

@app.get("/metrics/efficiency")
def get_efficiency():
    """Calculate sync efficiency"""
    if not sync_metrics:
        return {"efficiency": 0, "wasted_calls": 0}
    
    total = len(sync_metrics)
    # Assume syncs with 0 rows written are "wasted"
    wasted = sum(1 for m in sync_metrics if m["rows_written"] == 0)
    
    return {
        "total_syncs": total,
        "wasted_syncs": wasted,
        "efficiency": ((total - wasted) / total) * 100,
        "api_calls_saved_potential": wasted
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