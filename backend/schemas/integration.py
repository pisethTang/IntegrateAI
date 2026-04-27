from typing import Optional

from pydantic import BaseModel


class IntegrationSummary(BaseModel):
    id: str
    name: str
    status: str
    source: str
    target: str
    last_sync: Optional[str] = None
    next_sync: Optional[str] = None
    sync_count: int = 0
