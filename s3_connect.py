from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import StreamingResponse
import boto3
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
from typing import Optional
from io import BytesIO
from datetime import datetime
from pydantic import BaseModel
import uvicorn

# Load environment variables (you'll need to create a .env file with AWS credentials)
load_dotenv()

# AWS S3 Configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# Create a FastAPI app instance - can be imported by main app
app = FastAPI()

class S3FileResponse(BaseModel):
    file_name: str
    file_url: str
    file_size: int

# Initialize S3 client
def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

# Initialize S3 resource
def get_s3_resource():
    return boto3.resource(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

# Check connection and bucket existence
@app.get("/s3/check-connection")
async def check_s3_connection():
    try:
        s3 = get_s3_client()
        response = s3.list_buckets()
        all_buckets = [bucket['Name'] for bucket in response['Buckets']]
        
        if AWS_BUCKET_NAME in all_buckets:
            return {
                "status": "success", 
                "message": "Successfully connected to S3", 
                "bucket_exists": True,
                "all_buckets": all_buckets
            }
        else:
            return {
                "status": "warning",
                "message": "Connected to S3 but specified bucket does not exist",
                "bucket_exists": False,
                "all_buckets": all_buckets
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to S3: {str(e)}")

# List all buckets
@app.get("/s3/buckets")
async def list_buckets():
    try:
        s3 = get_s3_client()
        response = s3.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        return {"buckets": buckets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list buckets: {str(e)}")

# List objects in a bucket
@app.get("/s3/objects")
async def list_objects(prefix: Optional[str] = None):
    try:
        s3 = get_s3_client()
        params = {"Bucket": AWS_BUCKET_NAME}
        if prefix:
            params["Prefix"] = prefix
            
        response = s3.list_objects_v2(**params)
        
        if 'Contents' not in response:
            return {"objects": []}
            
        objects = [
            {
                "key": obj['Key'],
                "size": obj['Size'],
                "last_modified": obj['LastModified'].isoformat()
            } 
            for obj in response['Contents']
        ]
        return {"objects": objects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list objects: {str(e)}")

# Upload a file to S3
@app.post("/s3/upload", response_model=S3FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    folder: Optional[str] = None,
    s3_client = Depends(get_s3_client)
):
    try:
        # Read file content
        content = await file.read()
        
        # Generate a unique filename to prevent overwriting
        file_name, file_extension = os.path.splitext(file.filename)
        unique_filename = file_name +'_dt_' + datetime.now().strftime("%Y%m%d_%H%M%S") + file_extension
        
        # Create the S3 key (path)
        s3_key = unique_filename
        if folder:
            s3_key = f"{folder}/{unique_filename}"
        
        # Upload to S3
        s3_client.upload_fileobj(
            BytesIO(content),
            AWS_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": file.content_type}
        )
        
        # Generate a URL for the uploaded file
        file_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        
        return S3FileResponse(
            file_name=s3_key,
            file_url=file_url,
            file_size=len(content)
        )
    except S3UploadFailedError as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Download a file from S3
@app.get("/s3/download/{key}")
async def download_file(key: str, s3_client = Depends(get_s3_client)):
    try:
        # Get the object from S3
        response = s3_client.get_object(Bucket=AWS_BUCKET_NAME, Key=key)
        
        # Extract content and content type
        content = response['Body'].read()
        content_type = response.get('ContentType', 'application/octet-stream')
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={key.split('/')[-1]}"}
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise HTTPException(status_code=404, detail=f"File {key} not found")
        raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

# Delete a file from S3
@app.delete("/s3/delete/{key}")
async def delete_file(key: str, s3_client = Depends(get_s3_client)):
    try:
        s3_client.delete_object(Bucket=AWS_BUCKET_NAME, Key=key)
        return {"status": "success", "message": f"File {key} deleted successfully"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("s3_connect:app", host="0.0.0.0", port=8000, reload=True)