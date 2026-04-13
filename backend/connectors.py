import requests
from pyairtable import Api as AirtableApi
from typing import List, Dict

import logging

# logger init 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

class AirtableConnector:
    def __init__(self, api_key: str, base_id: str):
        self.api = AirtableApi(api_key)
        self.base = self.api.base(base_id)
    
    def get_tables(self) -> List[str]:
        """List all tables in base"""
        tables = list(self.base.schema().values())
        return [t.name for t in tables]
    
    def create_records(self, table_name: str, records: List[Dict]) -> Dict:
        """Create records in Airtable"""
        table = self.base.table(table_name)
         # DEBUG: Print what we're sending
        print("=" * 50)
        print(f"Table: {table_name}")
        print(f"Records to create: {len(records)}")
        for i, r in enumerate(records):
            print(f"  Record {i}: {r}")
        print("=" * 50)
        created = table.batch_create(records)

        # DEBUG: Print what Airtable returned
        print(f"Created: {len(created)} records")
        for c in created:
            print(f"  ID: {c['id']}, Fields: {c['fields']}")
        return {"created": len(created), "records": created}

class SyncEngine:
    def __init__(self, source_config: Dict, target_config: Dict, field_mapping: Dict = None):
        self.source = self._create_connector(source_config)
        self.target = self._create_connector(target_config)
        # Field mapping is configured at the integration level in main.py.
        # Keep source_config fallback for backwards compatibility.
        self.field_mapping = field_mapping or source_config.get("field_mapping", {})
    
    def _create_connector(self, config: Dict):
        if config["type"] == "google_sheets":
            return GoogleSheetsConnector(config["api_key"])
        elif config["type"] == "airtable":
            return AirtableConnector(config["api_key"], config["base_id"])
        raise ValueError(f"Unknown connector type: {config['type']}")
    
    def sync(self, source_id: str, target_table: str, range_name: str = "Sheet1") -> Dict:
        # 1. Read from Google Sheets
        source_data = self.source.get_sheet_data(source_id, range_name)

        if not self.field_mapping:
            raise ValueError("Field mapping is empty. Add field_mapping to the integration config.")
        
        # 2. Transform (map fields)
        transformed = []
        for row in source_data:
            new_row = {}
            for source_field, target_field in self.field_mapping.items():
                new_row[target_field] = row.get(source_field)
            if new_row:
                transformed.append(new_row)

        if not transformed:
            return {
                "status": "success",
                "rows_read": len(source_data),
                "rows_written": 0,
                "errors": ["No rows matched field mapping; nothing was written."]
            }
        
        # 3. Write to Airtable
        result = self.target.create_records(target_table, transformed)
        
        return {
            "status": "success",
            "rows_read": len(source_data),
            "rows_written": result["created"],
            "errors": []
        }