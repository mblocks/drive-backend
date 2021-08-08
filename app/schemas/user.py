from typing import Optional
from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: Optional[int] = None
    third: Optional[str] = None
    third_user_id: Optional[str] = None
    third_user_name: Optional[str] = None
