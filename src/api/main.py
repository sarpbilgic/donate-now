from fastapi import FastAPI
from src.core.config import config
from mangum import Mangum

@app.get("/")
def read_root():
    return {"message": "Welcome to the Donate Now API"}

app = FastAPI()
handler = Mangum(app)