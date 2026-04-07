from pydantic import BaseModel
from typing import List, Optional

class Summary(BaseModel):
    total_programs: int
    avg_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    budget_programs: int
    budget_share: Optional[float]

class Series(BaseModel):
    labels: List[str]
    values: List[float]