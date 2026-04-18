import random
from datetime import datetime, timedelta

def generate_realistic_sync_pattern(hours=24):
    """Generate sync pattern showing when data actually changes"""
    pattern = []
    
    for hour in range(hours):
        # Business hours (9-5) have more changes
        if 9 <= hour <= 17:
            changes = random.randint(0, 10)
        else:
            changes = random.randint(0, 2)
        
        pattern.append({
            "hour": hour,
            "data_changes": changes,
            "should_sync": changes > 0
        })
    
    return pattern

# Example output:
# Hour 9: 8 changes → Should sync
# Hour 10: 0 changes → Don't sync (save API call)
# Hour 11: 5 changes → Should sync