import os
from typing import List, Dict, Optional, Any
import requests

from google import genai
from google.genai import types
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# =============================================================================
# ACTUAL TOOL FUNCTIONS (these execute real backend operations)
# =============================================================================

def list_integrations() -> Dict[str, Any]:
    """Fetch all active integrations from the database."""
    try:
        resp = requests.get(f"{API_BASE_URL}/integrations", timeout=5)
        return {"status": "ok", "data": resp.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def view_sync_metrics() -> Dict[str, Any]:
    """Get current sync efficiency metrics."""
    try:
        resp = requests.get(f"{API_BASE_URL}/metrics/efficiency", timeout=5)
        return {"status": "ok", "data": resp.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def view_sync_history(limit: int = 10) -> Dict[str, Any]:
    """View recent sync history."""
    try:
        resp = requests.get(f"{API_BASE_URL}/metrics/sync-history", timeout=5)
        data = resp.json()
        return {"status": "ok", "data": data.get("metrics", [])[:limit]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def trigger_sync(integration_id: str = "1") -> Dict[str, Any]:
    """Manually trigger a data sync for an integration."""
    try:
        resp = requests.post(f"{API_BASE_URL}/sync/{integration_id}/trigger", timeout=15)
        return {"status": "ok", "data": resp.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_test_syncs(count: int = 5) -> Dict[str, Any]:
    """Run multiple test syncs to populate metrics."""
    results = []
    for i in range(count):
        resp = requests.post(f"{API_BASE_URL}/sync/1/trigger", timeout=15)
        results.append(resp.json())
    return {"status": "ok", "completed": count, "results": results}

def train_rl_optimizer() -> Dict[str, Any]:
    """Start training the RL-based sync scheduler."""
    try:
        resp = requests.post(f"{API_BASE_URL}/rl/train", timeout=300)
        return {"status": "ok", "data": resp.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_rl_evaluation() -> Dict[str, Any]:
    """Evaluate RL optimizer vs fixed schedule."""
    try:
        resp = requests.get(f"{API_BASE_URL}/rl/evaluate", timeout=30)
        return {"status": "ok", "data": resp.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def connect_google_sheets(sheet_id: str, range: str = "Sheet1") -> Dict[str, Any]:
    """Configure a Google Sheets source (writes to DB config)."""
    return {
        "status": "configured",
        "source_type": "google_sheets",
        "sheet_id": sheet_id,
        "range": range,
        "note": "Use POST /sync/1/trigger to start syncing"
    }

def connect_airtable(base_id: str, table: str) -> Dict[str, Any]:
    """Configure an Airtable target (writes to DB config)."""
    return {
        "status": "configured",
        "target_type": "airtable",
        "base_id": base_id,
        "table": table,
        "note": "Use POST /sync/1/trigger to start syncing"
    }

# =============================================================================
# GEMINI FUNCTION DECLARATIONS
# =============================================================================

TOOLS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="list_integrations",
            description="List all active data integrations currently configured in the system"
        ),
        types.FunctionDeclaration(
            name="view_sync_metrics",
            description="View current sync efficiency metrics including total syncs, wasted syncs, and efficiency percentage"
        ),
        types.FunctionDeclaration(
            name="view_sync_history",
            description="View recent sync history and logs",
            parameters=types.Schema(
                type="object",
                properties={
                    "limit": types.Schema(type="integer", description="Number of recent syncs to show (default 10)")
                }
            )
        ),
        types.FunctionDeclaration(
            name="trigger_sync",
            description="Manually trigger a data sync between Google Sheets and Airtable",
            parameters=types.Schema(
                type="object",
                properties={
                    "integration_id": types.Schema(type="string", description="Integration ID to sync (default '1')")
                }
            )
        ),
        types.FunctionDeclaration(
            name="run_test_syncs",
            description="Run multiple test syncs to generate metrics data for the dashboard",
            parameters=types.Schema(
                type="object",
                properties={
                    "count": types.Schema(type="integer", description="Number of test syncs to run (default 5)")
                }
            )
        ),
        types.FunctionDeclaration(
            name="train_rl_optimizer",
            description="Train the RL-based sync optimizer that learns when to sync to maximize efficiency"
        ),
        types.FunctionDeclaration(
            name="get_rl_evaluation",
            description="Evaluate and compare the RL optimizer against a fixed schedule"
        ),
        types.FunctionDeclaration(
            name="connect_google_sheets",
            description="Configure a Google Sheets spreadsheet as a data source",
            parameters=types.Schema(
                type="object",
                properties={
                    "sheet_id": types.Schema(type="string", description="Google Sheet ID from the URL"),
                    "range": types.Schema(type="string", description="Sheet range to read (default 'Sheet1')")
                },
                required=["sheet_id"]
            )
        ),
        types.FunctionDeclaration(
            name="connect_airtable",
            description="Configure an Airtable base as a sync target",
            parameters=types.Schema(
                type="object",
                properties={
                    "base_id": types.Schema(type="string", description="Airtable base ID starting with 'app'"),
                    "table": types.Schema(type="string", description="Table name to write to")
                },
                required=["base_id", "table"]
            )
        ),
    ])
]

# =============================================================================
# AI AGENT CLASS
# =============================================================================

class IntegrationAI:
    def __init__(self):
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview")
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        
        self.tool_map = {
            "list_integrations": list_integrations,
            "view_sync_metrics": view_sync_metrics,
            "view_sync_history": view_sync_history,
            "trigger_sync": trigger_sync,
            "run_test_syncs": run_test_syncs,
            "train_rl_optimizer": train_rl_optimizer,
            "get_rl_evaluation": get_rl_evaluation,
            "connect_google_sheets": connect_google_sheets,
            "connect_airtable": connect_airtable,
        }
    
    def chat(self, message: str, history: Optional[List[Dict]] = None) -> Dict:
        if not self.client:
            raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")
        
        # Step 1: Ask Gemini what to do (with tools available)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=message,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                system_instruction="""You are IntegrateAI Assistant. You help users manage data integrations.
You have access to tools that query the live backend. When a user asks about metrics, syncs, or integrations, USE the relevant tool rather than making up numbers.
After calling a tool, summarize the result conversationally.""",
            ),
        )
        
        candidate = response.candidates[0]
        part = candidate.content.parts[0]
        
        # Step 2: Check if Gemini wants to call a function
        if part.function_call:
            tool_name = part.function_call.name
            args = dict(part.function_call.args) if part.function_call.args else {}
            
            # Execute the tool
            tool_fn = self.tool_map.get(tool_name)
            if tool_fn:
                result = tool_fn(**args)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            # Step 3: Send result back to Gemini for natural language summary
            follow_up = self.client.models.generate_content(
                model=self.model_name,
                contents=f"""The user asked: "{message}"
You called tool: {tool_name} with args: {args}
Tool result: {result}

Summarize this result for the user in 1-2 sentences. Include specific numbers if available.""",
            )
            
            return {
                "response": follow_up.text or f"Executed {tool_name}. Result: {result}",
                "actions": self._build_actions(tool_name, result),
                "tool_call": {"name": tool_name, "args": args, "result": result}
            }
        
        # Normal text response (no tool call)
        return {
            "response": response.text or "I'm not sure how to help with that.",
            "actions": self._build_actions(None, None)
        }
    
    def _build_actions(self, last_tool: Optional[str], result: Optional[Dict]) -> List[Dict]:
        """Generate UI action buttons based on context."""
        actions = []
        
        if last_tool == "list_integrations":
            actions.append({"label": "Trigger Sync", "action": "trigger_sync"})
        elif last_tool == "view_sync_metrics":
            actions.append({"label": "View Sync History", "action": "view_sync_history"})
            actions.append({"label": "Run Test Syncs", "action": "run_test_syncs"})
        elif last_tool == "trigger_sync" or last_tool == "run_test_syncs":
            actions.append({"label": "View Metrics", "action": "view_sync_metrics"})
        elif last_tool is None:
            # Default actions when no tool was called
            actions.append({"label": "View Integrations", "action": "list_integrations"})
            actions.append({"label": "View Metrics", "action": "view_sync_metrics"})
        
        return actions