from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class QueryRequest(BaseModel):
    session_id: str
    query: str


class QueryResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    visualization: Optional[str] = None  # Base64 encoded image
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    query: str


class SessionInfo(BaseModel):
    filename: str
    columns: List[str]
    shape: List[int]
    created_at: str