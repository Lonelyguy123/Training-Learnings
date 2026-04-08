from fastapi import FastAPI
from database import engine, Base
from routers import items

# Create all tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Items API", version="1.0.0")

app.include_router(items.router)

@app.get("/")
def root():
    return {"message": "API is running"}