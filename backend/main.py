from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os 
import logging

from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))



# Import the connectors you created
from connectors import SyncEngine, GoogleSheetsConnector, AirtableConnector
from ai_agent import IntegrationAI


# Initialize AI agent
ai_agent = IntegrationAI()

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

@app.post("/sync/{integration_id}/trigger")
def trigger_sync(integration_id: str):
    """Actually perform the sync using real connectors"""
    config = integration_configs.get(integration_id)
    if not config:
        return {"status": "error", "message": "Integration not found"}
    
    try:
        engine = SyncEngine(
            config["source"],
            config["target"],
            config.get("field_mapping", {})
        )
        result = engine.sync(
            config["source"]["sheet_id"],
            config["target"]["table"],
            config["source"].get("range", "Sheet1")
        )
        return result
    except Exception as e:
        logging.error(f"Error during sync: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)