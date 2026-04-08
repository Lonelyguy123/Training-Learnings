from pydantic import BaseModel
from typing import Optional

# Shared base
class ItemBase(BaseModel):
    name:        str
    description: Optional[str] = None
    price:       float
    is_active:   bool = True

# Used on POST (no id yet)
class ItemCreate(ItemBase):
    pass

# Used on PUT (all fields optional)
class ItemUpdate(BaseModel):
    name:        Optional[str]   = None
    description: Optional[str]   = None
    price:       Optional[float] = None
    is_active:   Optional[bool]  = None

# Returned in responses (includes id)
class ItemResponse(ItemBase):
    id: int

    class Config:
        from_attributes = True   # orm_mode in Pydantic v1