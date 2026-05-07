from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
import os 
from dotenv import load_dotenv

load_dotenv()

jobstores = {
    'default': MongoDBJobStore(
        database='ASHA',
        collection='workflows',
        host=os.getenv("MONGO_URL")
    )
}

scheduler = BackgroundScheduler(jobstores=jobstores)
