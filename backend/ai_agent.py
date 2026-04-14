import os
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class IntegrationAI:
    def __init__(self):
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.model = genai.GenerativeModel(model_name)
        
        self.system_prompt = """You are an AI assistant for IntegrateAI, a data integration platform.
Your job is to help users connect systems and sync data.

Available integrations:
- Google Sheets
- Airtable
- PostgreSQL databases

When a user wants to connect systems:
1. Ask which source they want to connect
2. Ask which target they want to sync to
3. Offer to help with authentication

Respond conversationally and offer specific actions the user can take."""
    
    def chat(self, message: str, history: List[Dict] = None) -> Dict:
        """Process user message and return AI response with actions"""
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")
        
        # Build conversation
        chat = self.model.start_chat(history=[])
        
        # Add system context
        chat.send_message(self.system_prompt)
        
        # Get response
        response = chat.send_message(message)
        ai_text = response.text
        
        # Extract actions from response (simple parsing)
        actions = self._extract_actions(ai_text)
        
        return {
            "response": ai_text,
            "actions": actions
        }
    
    def _extract_actions(self, text: str) -> List[Dict]:
        """Extract suggested actions from AI response"""
        actions = []
        
        # Simple keyword-based action detection
        if "google sheet" in text.lower() or "sheets" in text.lower():
            actions.append({"label": "Connect Google Sheets", "action": "auth_sheets"})
        if "airtable" in text.lower():
            actions.append({"label": "Connect Airtable", "action": "auth_airtable"})
        if "database" in text.lower() or "postgres" in text.lower():
            actions.append({"label": "Connect Database", "action": "auth_database"})
        if "sync" in text.lower():
            actions.append({"label": "View Integrations", "action": "view_integrations"})
        
        return actions