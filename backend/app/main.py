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

# Behind CloudFront the API is served from the same domain as the frontend
# under /api, which removes the cross-origin request (and the mixed-content
# block that an HTTPS page calling an HTTP origin would otherwise hit). The
# prefix is configurable so the Render deployment, where the API has its own
# hostname, keeps working with no prefix at all.
for router in (auth.router, tickets.router, dashboard.router, users.router):
    app.include_router(router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    """Deliberately unprefixed: container health checks hit this directly."""
    return {"status": "ok"}
