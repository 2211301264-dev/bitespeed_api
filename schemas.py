from pydantic import BaseModel
from typing import List, Optional


class IdentifyRequest(BaseModel):
    email: Optional[str] = None
    phoneNumber: Optional[str] = None

    class Config:
        from_attributes = True


class ContactResponse(BaseModel):
    primaryContatctId: int
    emails: List[str]
    phoneNumbers: List[str]
    secondaryContactIds: List[int]

    class Config:
        from_attributes = True


class IdentifyResponse(BaseModel):
    contact: ContactResponse

    class Config:
        from_attributes = True
