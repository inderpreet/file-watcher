from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api import api, limiter
from src.logger import logger
from src.storage.db import init_file_details_table


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started")
    init_file_details_table()
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="File Watch",
    description="File management and backup API",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.include_router(api)


@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request):
    return {"message": "Hello, World!", "docs": "/docs", "api": "/api/v1"}


def main():
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
