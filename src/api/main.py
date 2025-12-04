import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from api import routers
from starlette.middleware.base import BaseHTTPMiddleware


app = FastAPI(
    root_path="/Prod"  
)

# CORS Middleware for FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Custom middleware to add CORS headers to ALL responses (for API Gateway)
class CORSHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token, stripe-signature"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

app.add_middleware(CORSHeaderMiddleware)

# Handle OPTIONS requests explicitly for API Gateway
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token, stripe-signature",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to the Donate Now API"}


app.include_router(routers.router)

handler = Mangum(app)