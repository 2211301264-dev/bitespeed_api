from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from schemas import IdentifyRequest, IdentifyResponse, ContactResponse
from reconciliation import reconcile_identity, build_response_data

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/identify", response_model=IdentifyResponse)
def identify(request: IdentifyRequest, db: Session = Depends(get_db)):
    try:
        primary_contact, _ = reconcile_identity(
            db,
            request.email,
            request.phoneNumber
        )
        response_data = build_response_data(db, primary_contact)
        return IdentifyResponse(contact=ContactResponse(**response_data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
