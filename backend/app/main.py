from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .config import settings
from .database import Base, engine
from .routers import auth, tickets, dashboard, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="IT Helpdesk API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(dashboard.router)
app.include_router(users.router)


@app.get("/health")
def health():
    return {"status": "ok"}
