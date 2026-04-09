"""
Main application module for the FastAPI assessment.
Sets up the FastAPI app, middleware, routers, and database connections.
"""

import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from db.session import engine
from models.base import Base
from routers.auth import router as auth_router
from routers.user import router as user_router
from routers.vector_db import router as vector_db_router
from routers.workflow import router as workflow_router
from routers.deps import get_current_user

logger = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
async def startup():
    """
    this function run when the application start
    """
    async with engine.begin() as conn:

        # This will create all the tables in the database
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router, dependencies=[Depends(get_current_user)])
app.include_router(vector_db_router, dependencies=[Depends(get_current_user)])
app.include_router(workflow_router, dependencies=[Depends(get_current_user)])


@app.on_event("shutdown")
async def shutdown():
    """
    this function run when the application shutdown
    """
    await engine.dispose()
    logger.info("Database connection closed successfully")
