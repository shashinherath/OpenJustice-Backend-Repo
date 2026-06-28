from typing import List, Optional
from pydantic import BaseModel

class CollectionCount(BaseModel):
    collection_id: str
    count: int

class LetterCount(BaseModel):
    letter: str
    count: int

class LibraryCollectionsResponse(BaseModel):
    collections: List[CollectionCount]

class LibraryLettersResponse(BaseModel):
    collection_id: str
    letters: List[LetterCount]
