from fastapi import FastAPI
from .api_routes import router

app = FastAPI(title="Chat with PDF")
app.include_router(router)

