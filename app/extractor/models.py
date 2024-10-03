from typing import List, Optional

from pydantic import BaseModel


class AnimalID(BaseModel):
    id: int


class AnimalRaw(BaseModel):
    id: int
    name: str
    born_at: Optional[int] = None
    friends: Optional[str] = None


class Animal(BaseModel):
    id: int
    name: str
    born_at: Optional[str] = None
    friends: List[str] = []
