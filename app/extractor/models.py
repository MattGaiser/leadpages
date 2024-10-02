from typing import Optional, List

from pydantic import BaseModel


class AnimalID(BaseModel):
    id: int

    class Config:
        allow_mutation = True


class AnimalRaw(BaseModel):
    id: int
    name: str
    born_at: Optional[int] = None
    friends: Optional[str] = None

    class Config:
        allow_mutation = True


class Animal(BaseModel):
    id: int
    name: str
    born_at: Optional[str] = None
    friends: List[str] = []

    class Config:
        allow_mutation = True