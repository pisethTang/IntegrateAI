import random
import time
from datetime import datetime, timedelta
from Connectors.GoogleSheetsConnector import GoogleSheetsConnector
import os

class TrafficSimulator:
    """Simulates realistic data patterns for testing RL optimizer"""
    
    def __init__(self, sheet_id: str, api_key: str):
        self.sheets = GoogleSheetsConnector(api_key)
        self.sheet_id = sheet_id
        self.hour = 0
        self.day = 0  # 0=Mon, 6=Sun
        
        # Base data template
        self.base_data = [
            {"Name": "Project A", "Status": "Active", "Due Date": "2024-06-01"},
            {"Name": "Project B", "Status": "Completed", "Due Date": "2024-05-15"},
            {"Name": "Project C", "Status": "In Progress", "Due Date": "2024-07-01"},
        ]
    
    def get_change_probability(self) -> float:
        """Returns probability of data change based on time patterns"""
        
        # Monday morning rush (high activity)
        if self.day == 0 and 9 <= self.hour <= 11:
            return 0.8  # 80% chance of change
        
        # Friday afternoon (urgent requests)
        elif self.day == 4 and 16 <= self.hour <= 18:
            return 0.7
        
        # Business hours (moderate)
        elif 9 <= self.hour <= 17 and self.day < 5:
            return 0.3
        
        # Weekends (very low)
        elif self.day >= 5:
            return 0.05
        
        # Off-hours (low)
        else:
            return 0.1
    
    def simulate_tick(self):
        """Simulate one hour passing"""
        should_change = random.random() < self.get_change_probability()
        
        if should_change:
            # Randomly modify data
            new_data = self.generate_new_data()
            self.write_to_sheet(new_data)
            print(f"[{self.day_name()} {self.hour:02d}:00] DATA CHANGED (prob: {self.get_change_probability():.1%})")
            result = True
        else:
            print(f"[{self.day_name()} {self.hour:02d}:00] No change (prob: {self.get_change_probability():.1%})")
            result = False
        
        # Advance time 
        self.hour += 1
        if self.hour >= 24:
            self.hour = 0
            self.day = (self.day + 1) % 7
        
        return result
    
    def generate_new_data(self) -> list:
        """Generate slightly modified data"""
        statuses = ["Active", "Completed", "In Progress", "On Hold"]
        new_data = []
        
        for i, row in enumerate(self.base_data):
            new_row = row.copy()
            # Randomly change status
            if random.random() < 0.5:
                new_row["Status"] = random.choice(statuses)
            new_data.append(new_row)
        
        # Occasionally add new row
        if random.random() < 0.3:
            new_data.append({
                "Name": f"Project {chr(68 + len(new_data))}",
                "Status": random.choice(statuses),
                "Due Date": "2024-08-01"
            })
        
        return new_data
    
    def write_to_sheet(self, data: list):
        """Write data to Google Sheet (simulation)"""
        # In real implementation, this would use Google Sheets API
        # For now, just track that we "wrote" data
        pass
    
    def day_name(self) -> str:
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return days[self.day]
    
    def run_simulation(self, hours: int = 168):  # 1 week
        """Run full simulation"""
        print(f"=== Simulating {hours} hours of traffic ===\n")
        
        changes = 0
        for _ in range(hours):
            if self.simulate_tick():
                changes += 1
        
        print(f"\n=== Summary ===")
        print(f"Total hours: {hours}")
        print(f"Data changes: {changes}")
        print(f"Change rate: {changes/hours:.1%}")

if __name__ == "__main__":
    simulator = TrafficSimulator(
        sheet_id=os.getenv("GOOGLE_SHEET_ID"),
        api_key=os.getenv("GOOGLE_SHEETS_API_KEY")
    )
    simulator.run_simulation(hours=168)  # 1 week