
from typing import List, Dict
from pyairtable import Api as AirtableApi

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
