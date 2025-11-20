from fastapi import FastAPI
from mangum import Mangum
from api import routers


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Donate Now API"}


app.include_router(routers.router)

handler = Mangum(app)