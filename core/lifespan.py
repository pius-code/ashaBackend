from dotenv import load_dotenv
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
import os
from beanie import init_beanie
from utils.logger import logger, tlogger, xlogger
from model import document_models as all_models
from core.mqtt import client
from core.scheduler import scheduler

load_dotenv()


def create_lifespan(mcp_app):
    @asynccontextmanager
    async def lifespan(app):
        """Lifespan context manager for FastAPI app"""
        mongo_client = None
        try:
            async with mcp_app.lifespan(app):
                mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
                await init_beanie(
                    database=mongo_client.get_default_database(),
                    document_models=all_models,
                )
                logger.info(f"Connected to MongoDB with {len(all_models)} document models") # noqa
                client.loop_start()
                tlogger.info("Connected TO MQTT")
                scheduler.start()
                xlogger.info("scheduler started")
                yield

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            raise
        finally:
            if mongo_client is not None:
                logger.info("Disconnecting from MongoDB...")
                mongo_client.close()
                logger.info("Disconnected from MongoDB")
                client.loop_stop()
                tlogger.info("Disconnected from MQTT")
                if scheduler.running:
                    scheduler.shutdown()
                xlogger.info("scheduler stopped")

    return lifespan
