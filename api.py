import shutil
from dotenv import load_dotenv
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from datetime import datetime
import uvicorn
from s3_connect import upload_file as s3_upload, get_s3_client

load_dotenv()

app = FastAPI()

@app.post("/upload-template")
async def upload_s10_template(file: UploadFile = File(...)):
    try:
        # generate file name
        file_name, file_extension = os.path.splitext(file.filename)
        curr_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = file_name + "_" + curr_timestamp
        file_name = file_name + file_extension
        # TODO: upload to local file /tmp/s10-template
        upload_dir = "/tmp/s10-template"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file_name)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        # TODO: upload to S3
        s3_response = await s3_upload(file, s3_client=get_s3_client())
        # TODO: upload metadata to database
        # invoke cli for keys
        # get a json of the list of keys generated
        # return success message
        return s3_response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("s3_connect:app", host="0.0.0.0", port=8000, reload=True)