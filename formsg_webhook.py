from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, DateTime, JSON, String, ForeignKey
from datetime import datetime
import json
import formsg
import os
from pydantic import BaseModel
import shutil
from dotenv import load_dotenv
from s3_connect import upload_file as s3_upload, get_s3_client
import uuid
import uvicorn

DATABASE_URL = "sqlite+aiosqlite:///./dev.db"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

# Schema Models
class Template(Base):
    __tablename__ = "templates"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'templateID' not in kwargs:
            self.templateID = str(uuid.uuid4())
        if 'createdAt' not in kwargs:
            self.createdAt = datetime.utcnow()
        if 'updatedAt' not in kwargs:
            self.updatedAt = datetime.utcnow()
    
    templateID = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    keys = Column(JSON, nullable=False)
    createdAt = Column(DateTime, nullable=False)
    updatedAt = Column(DateTime, nullable=False)

class Package(Base):
    __tablename__ = "packages"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = str(uuid.uuid4())
        if 'files' not in kwargs:
            self.files = []
        if 'createdAt' not in kwargs:
            self.createdAt = datetime.utcnow()
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    templateID = Column(String, ForeignKey('templates.templateID'), nullable=False)
    data = Column(JSON, nullable=False)
    files = Column(JSON, nullable=False)
    createdAt = Column(DateTime, nullable=False)

class FormA(Base):
    __tablename__ = "FormA"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = str(uuid.uuid4())
        if 'createdAt' not in kwargs:
            self.createdAt = datetime.utcnow()
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    createdBy = Column(String(255), nullable=False)
    data = Column(JSON, nullable=False)
    createdAt = Column(DateTime, nullable=False)

class File(Base):
    __tablename__ = "files"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'id' not in kwargs:
            self.id = str(uuid.uuid4())
        if 'uploadedAt' not in kwargs:
            self.uploadedAt = datetime.utcnow()
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    uploadedAt = Column(DateTime, nullable=False)


app = FastAPI()

# Set your FormSG secret key (replace with your actual key or use env var)
FORM_SECRET_KEY = "AsrsyzbV7vWlfOgK7jQBHe62z1NLeLc5hYWTcJ8LcGY="

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def insert_template(name: str, keys: dict) -> str:
    """
    Insert a new template into the database.
    
    Args:
        name (str): The name of the template
        keys (dict): The keys data for the template
        
    Returns:
        str: The templateID of the created template
    """
    try:
        current_time = datetime.utcnow()
        async with async_session() as session:
            new_template = Template(
                name=name,
                keys=keys,
                createdAt=current_time,
                updatedAt=current_time
            )
            session.add(new_template)
            await session.commit()
            await session.refresh(new_template)
            return new_template.templateID
    except Exception as e:
        raise Exception(f"Failed to create template: {str(e)}")

@app.get("/templates")
async def get_templates():
    async with async_session() as session:
        result = await session.execute(
            Template.__table__.select()
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

@app.post("/upload-template")
async def upload_s10_template(file: UploadFile):
    try:
        # Read the file content first
        file_content = await file.read()
        
        # Parse JSON content
        json_content = json.loads(file_content)
        
        # generate file name
        file_name, file_extension = os.path.splitext(file.filename)
        curr_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = file_name + "_" + curr_timestamp
        file_name = file_name + file_extension
        
        # Save to local file
        upload_dir = "/tmp/s10-template"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_content)
            
        # Reset file pointer for S3 upload
        await file.seek(0)
        s3_response = await s3_upload(file, s3_client=get_s3_client())
        
        # Create template record with JSON content as keys
        template_id = await insert_template(name=file_name, keys=json_content)
        return {"template_id": template_id, "s3_response": s3_response.json()}
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("formsg_webhook:app", host="0.0.0.0", port=8000, reload=True)