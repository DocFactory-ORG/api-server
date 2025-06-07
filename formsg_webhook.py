from fastapi import FastAPI, Request
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, DateTime, JSON
from datetime import datetime
import json
import formsg
import os
from pydantic import BaseModel

DATABASE_URL = "sqlite+aiosqlite:///./dev.db"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class FormSubmission(Base):
    __tablename__ = "form_submissions"
    id = Column(Integer, primary_key=True, index=True)
    submission = Column(JSON)
    submitted_at = Column(DateTime, default=datetime.utcnow)

class FormSGData(BaseModel):
    formId: str
    submissionId: str
    encryptedContent: str
    version: float
    created: str
    attachmentDownloadUrls: dict
    paymentContent: dict

class FormSGPayload(BaseModel):
    data: FormSGData

app = FastAPI()

# Set your FormSG secret key (replace with your actual key or use env var)
FORM_SECRET_KEY = "AsrsyzbV7vWlfOgK7jQBHe62z1NLeLc5hYWTcJ8LcGY="

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/formsg-webhook")
async def receive_formsg(payload: FormSGPayload):
    encrypted_content = payload.data.encryptedContent
    if not encrypted_content:
        return {"error": "Missing encryptedContent in payload"}

    # Decrypt using formsg-python-sdk
    sdk = formsg.FormSdk("PRODUCTION")  # or "STAGING" if using staging
    try:
        decrypted = sdk.crypto.decrypt(FORM_SECRET_KEY, {"encryptedContent": encrypted_content})
    except Exception as e:
        return {"error": f"Decryption failed: {str(e)}"}

    # Store the decrypted responses in the DB
    async with async_session() as session:
        submission = FormSubmission(submission=decrypted)
        session.add(submission)
        await session.commit()
    return {"status": "received", "decrypted": decrypted}

@app.get("/submissions")
async def get_submissions():
    async with async_session() as session:
        result = await session.execute(
            FormSubmission.__table__.select()
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    