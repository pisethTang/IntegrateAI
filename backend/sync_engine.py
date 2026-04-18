import json

# import requests
from typing import List, Dict


import hashlib

import logging

# logger init 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# import connectors from Connectors/ folder 
from Connectors.GoogleSheetsConnector import GoogleSheetsConnector
from Connectors.AirTableConnector import AirtableConnector





class SyncEngine:
    def __init__(self, source_config: Dict, target_config: Dict, field_mapping: Dict):
        self.source = self._create_connector(source_config)
        self.target = self._create_connector(target_config)
        # Field mapping is configured at the integration level in main.py.
        # Keep source_config fallback for backwards compatibility.
        self.field_mapping = field_mapping or source_config.get("field_mapping", {})
        self.last_sync_hash = None  # Track last sync state

    
    def _create_connector(self, config: Dict):
        if config["type"] == "google_sheets":
            return GoogleSheetsConnector(config["api_key"])
        elif config["type"] == "airtable":
            return AirtableConnector(config["api_key"], config["base_id"])
        raise ValueError(f"Unknown connector type: {config['type']}")
    
    def compute_hash(self, data: List[Dict]) -> str:
        """Compute a hash of the data for change detection"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def sync(self, source_id: str, target_table: str, range_name: str = "Sheet1") -> Dict:
        # 1. Read from Google Sheets
        source_data = self.source.get_sheet_data(source_id, range_name)

        if not self.field_mapping:
            raise ValueError("Field mapping is empty. Add field_mapping to the integration config.")
        # 2. Check if data changed using hash
        current_hash = self.compute_hash(source_data)
        if self.last_sync_hash == current_hash:
            return {
                "status": "success",
                "rows_read": len(source_data),
                "rows_written": 0,
                "errors": []
             }
        
        # 3. Transform (map fields)
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
        
        # 4. Write to Airtable
        result = self.target.create_records(target_table, transformed)
        
        # 5. Update sync hash on success
        self.last_sync_hash = current_hash  # Update the sync hash

        return {
            "status": "success",
            "rows_read": len(source_data),
            "rows_written": result["created"],
            "errors": []
        }