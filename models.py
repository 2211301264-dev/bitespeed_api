from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    phoneNumber = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True, index=True)
    linkedId = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    linkPrecedence = Column(String, default="primary")  # "primary" or "secondary"
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deletedAt = Column(DateTime, nullable=True)

    # Self-referential relationship
    linked_contact = relationship(
        "Contact",
        remote_side=[id],
        backref="secondary_contacts"
    )

    __table_args__ = (
        Index("idx_email", "email"),
        Index("idx_phone", "phoneNumber"),
        Index("idx_linkedId", "linkedId"),
    )

    class Config:
        from_attributes = True
