# initializations for mongodb client and also contains the lifeSpan
#  for the application(weird, I know)

from dotenv import load_dotenv
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
import os
from beanie import init_beanie
from utils.logger import logger
from model import __all__ as all_models


load_dotenv()


@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for FastAPI app"""
    mongo_client = None
    try:
        mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        await init_beanie(
            database=mongo_client.get_default_database(),  # type: ignore
            document_models=all_models,
        )
        logger.info(
            f"Connected to MongoDB with {len(all_models)} document models"
        )  # noqa

        yield

    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise
    finally:
        if mongo_client is not None:
            logger.info("Disconnecting from MongoDB...")
            mongo_client.close()
            logger.info("Disconnected from MongoDB")
