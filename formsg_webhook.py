from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/formsg-webhook")
async def receive_formsg(request: Request):
    data = await request.json()
    # For now, just return the received data
    return {"received": data} 