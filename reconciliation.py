from sqlalchemy.orm import Session
from models import Contact
from datetime import datetime
from typing import Tuple, List, Optional, Set


def get_all_linked_contacts(db: Session, email: Optional[str], phone: Optional[str]) -> List[Contact]:
 
    query = db.query(Contact).filter(Contact.deletedAt.is_(None))
    
    conditions = []
    if email:
        conditions.append(Contact.email == email)
    if phone:
        conditions.append(Contact.phoneNumber == phone)
    
    if not conditions:
        return []
    
    from sqlalchemy import or_
    direct_matches = query.filter(or_(*conditions)).all()
    
    if not direct_matches:
        return []
    
     
    all_contact_ids = set()
    visited = set()
    
    def collect_linked(contact: Contact):
        if contact.id in visited:
            return
        visited.add(contact.id)
        all_contact_ids.add(contact.id)
        
       
        if contact.linkedId and contact.linkedId not in visited:
            linked = db.query(Contact).filter(Contact.id == contact.linkedId).first()
            if linked:
                collect_linked(linked)
        
        
        secondaries = db.query(Contact).filter(Contact.linkedId == contact.id).all()
        for sec in secondaries:
            if sec.id not in visited:
                collect_linked(sec)
    
    for contact in direct_matches:
        collect_linked(contact)
    
    return db.query(Contact).filter(Contact.id.in_(all_contact_ids)).all()


def find_primary_contact(contacts: List[Contact]) -> Optional[Contact]:
   
    if not contacts:
        return None
    
    primary_contacts = [c for c in contacts if c.linkPrecedence == "primary"]
    if primary_contacts:
        return min(primary_contacts, key=lambda c: c.createdAt)
    
    return min(contacts, key=lambda c: c.createdAt)


def reconcile_identity(db: Session, email: Optional[str], phone: Optional[str]) -> Tuple[Contact, bool]:
  
    linked_contacts = get_all_linked_contacts(db, email, phone)
    
    if not linked_contacts:
        new_contact = Contact(
            email=email,
            phoneNumber=phone,
            linkPrecedence="primary"
        )
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        return new_contact, True

    primary_contact = find_primary_contact(linked_contacts)

    primary_contacts = [c for c in linked_contacts if c.linkPrecedence == "primary"]
    if len(primary_contacts) > 1:
        for contact in primary_contacts:
            if contact.id != primary_contact.id:  
                contact.linkedId = primary_contact.id
                contact.linkPrecedence = "secondary"
                contact.updatedAt = datetime.utcnow()
                db.add(contact)
        db.commit()
    
    has_new_email = email and email not in [c.email for c in linked_contacts if c.email]
    has_new_phone = phone and phone not in [c.phoneNumber for c in linked_contacts if c.phoneNumber]
    
    if has_new_email or has_new_phone:
        new_contact = Contact(
            email=email,
            phoneNumber=phone,
            linkedId=primary_contact.id,
            linkPrecedence="secondary"
        )
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        return primary_contact, True
    
    return primary_contact, False


def get_all_linked_contacts_for_primary(db: Session, primary_id: int) -> List[Contact]:
    primary = db.query(Contact).filter(Contact.id == primary_id).first()
    if not primary:
        return []
    
    all_ids = set()
    visited = set()
    
    def collect(contact_id: int):
        if contact_id in visited:
            return
        visited.add(contact_id)
        all_ids.add(contact_id)
        
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return
        
        if contact.linkedId:
            collect(contact.linkedId)
        
        secondaries = db.query(Contact).filter(Contact.linkedId == contact_id).all()
        for sec in secondaries:
            if sec.id not in visited:
                collect(sec.id)
    
    collect(primary_id)
    
    return db.query(Contact).filter(Contact.id.in_(all_ids)).all()


def build_response_data(db: Session, primary_contact: Contact) -> dict:
    all_contacts = get_all_linked_contacts_for_primary(db, primary_contact.id)
    
    emails = []
    if primary_contact.email:
        emails.append(primary_contact.email)
    
    for contact in all_contacts:
        if contact.email and contact.email not in emails and contact.id != primary_contact.id:
            emails.append(contact.email)
    
    phone_numbers = []
    if primary_contact.phoneNumber:
        phone_numbers.append(primary_contact.phoneNumber)
    
    for contact in all_contacts:
        if contact.phoneNumber and contact.phoneNumber not in phone_numbers and contact.id != primary_contact.id:
            phone_numbers.append(contact.phoneNumber)
    
    secondary_ids = [c.id for c in all_contacts if c.linkPrecedence == "secondary" and c.id != primary_contact.id]
    
    return {
        "primaryContatctId": primary_contact.id,
        "emails": emails,
        "phoneNumbers": phone_numbers,
        "secondaryContactIds": secondary_ids
    }
