import requests
from typing import List, Dict




class GoogleSheetsConnector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://sheets.googleapis.com/v4/spreadsheets"
    
    def get_sheet_data(self, spreadsheet_id: str, range_name: str = "Sheet1") -> List[Dict]:
        """Read data from a public Google Sheet"""
        url = f"{self.base_url}/{spreadsheet_id}/values/{range_name}?key={self.api_key}"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        values = data.get("values", [])
        
        if not values:
            return []
        
        # First row is headers
        headers = values[0]
        rows = []
        for row in values[1:]:
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = row[i] if i < len(row) else ""
            rows.append(row_dict)
        
        return rows


