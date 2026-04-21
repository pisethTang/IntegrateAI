import os
from typing import List, Dict, Optional

from google import genai
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class IntegrationAI:
    def __init__(self):
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.client = None
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        
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
    
    def chat(self, message: str, history: Optional[List[Dict]] = None) -> Dict:
        """Process user message and return AI response with actions"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")

        if self.client is None:
            self.client = genai.Client(api_key=api_key)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=message,
            config=genai.types.GenerateContentConfig(
                system_instruction=self.system_prompt,
            ),
        )
        ai_text = (response.text or "").strip()
        if not ai_text:
            raise RuntimeError("Gemini returned an empty response")
        
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