from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorSchema(BaseModel):
    """ Define como uma mensagem de erro será representada
    """
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
