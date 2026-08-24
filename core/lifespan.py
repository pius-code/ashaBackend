import asyncio
import threading
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
import os
from beanie import init_beanie
from utils.logger import logger, tlogger, xlogger
from model import document_models as all_models
from core.mqtt import client
from utils.mqtt import set_event_loop
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
                    database=mongo_client.get_default_database(),  # type: ignore # noqa
                    document_models=all_models,
                )
                logger.info(f"Connected to MongoDB with {len(all_models)} document models") # noqa
                scheduler.start()
                xlogger.info("scheduler started")
                set_event_loop(asyncio.get_running_loop())

                def _connect_with_retry():
                    import time
                    mqtt_ip = os.getenv("MQTT_IP", "d1fb95ffc6654d6e98effc66d26fed74.s1.eu.hivemq.cloud")  # noqa
                    mqtt_port = int(os.getenv("MQTT_PORT", "8883"))
                    for attempt in range(15):
                        try:
                            client.connect(mqtt_ip, mqtt_port, keepalive=60)
                            client.loop_start()
                            tlogger.info(f"Connected TO MQTT on attempt {attempt + 1}")  # noqa
                            return
                        except Exception as e:
                            delay = min(5 * (attempt + 1), 30)
                            tlogger.warning(f"MQTT attempt {attempt + 1} failed: {e} — retrying in {delay}s")  # noqa
                            time.sleep(delay)
                    tlogger.error("MQTT: All connection attempts exhausted")

                threading.Thread(target=_connect_with_retry, daemon=True).start() # noqa

                yield

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            raise
        finally:
            if mongo_client is not None:
                logger.info("Disconnecting from MongoDB...")
                mongo_client.close()
                logger.info("Disconnected from MongoDB")
                try:
                    client.loop_stop()
                    tlogger.info("Disconnected from MQTT")
                except Exception:
                    pass
                if scheduler.running:
                    scheduler.shutdown()
                xlogger.info("scheduler stopped")

    return lifespan
