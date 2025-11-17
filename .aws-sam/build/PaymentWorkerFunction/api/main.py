from fastapi import FastAPI
from src.core.config import config
from mangum import Mangum
from src.api import routers


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Donate Now API"}


app.include_router(routers.router)

handler = Mangum(app)