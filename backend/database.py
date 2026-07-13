import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "medai")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB_NAME]

chat_history_collection = db["chat_history"]
