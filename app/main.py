
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import check_database_connection
from app.logger import logger
from app.routes.chat import router as chat_router
from app.routes.orders import router as orders_router
from app.routes.support import router as support_router
from app.routes import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.APP_NAME)

    if not check_database_connection():
        logger.error("Application startup: database connection failed")
    else:
        logger.info("Application startup: database connection verified")

    yield

    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

local_frontend_origins = [
    f"http://{host}:{port}"
    for host in ("localhost", "127.0.0.1")
    for port in (3000, 4173, *range(5173, 5191))
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=local_frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(chat_router)
app.include_router(orders_router)
app.include_router(support_router)
app.include_router(auth.router)
@app.get("/health")
def health():
    return {"status": "ok"}
