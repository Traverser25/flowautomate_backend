# app/schemas/search.py
from pydantic import BaseModel, Field
from typing import Optional

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k_paragraphs: Optional[int] = Field(5, ge=1, le=20)
    top_k_tables: Optional[int] = Field(10, ge=1, le=20)
