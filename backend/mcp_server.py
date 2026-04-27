from typing import Dict, List


class MCPTool:
    def __init__(self, name: str, description: str, parameters: Dict):
        self.name = name
        self.description = description
        self.parameters = parameters



class MCPServer:
    """
    Model Context Protocol (MCP) Server implementation for IntegrateAI.
    """

    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self._register_default_tools()
    

    def _register_default_tools(self):
        self.tools["connect_google_sheets"] = MCPTool(
            name="connect_google_sheets",
            description="Connect to Google Sheets and retrieve data for data syncing.",
            parameters={
                "sheet_id": "string",
                "range": "string"
            }            
        )

        self.tools["connect_airtable"] = MCPTool(
            name="connect_airtable",
            description="Connect to an Airtable base to receive synced data",
            parameters={"base_id": "string", "table": "string"}
        )
        self.tools["trigger_sync"] = MCPTool(
            name="trigger_sync",
            description="Manually trigger a data sync between connected systems",
            parameters={"integration_id": "string"}
        )
        self.tools["view_metrics"] = MCPTool(
            name="view_metrics",
            description="View sync efficiency metrics and recent activity",
            parameters={}
        )

    def list_tools(self) -> List[Dict]:
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self.tools.values()
        ]
    
    def call_tool(self, tool_name: str, params: Dict) -> Dict:
        tool = self.tools.get(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        return {"status": "called", "tool": tool_name, "params": params}

# Global instance
mcp_server = MCPServer()