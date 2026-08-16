import os

from dotenv import load_dotenv
from pymongo import MongoClient

# Loads the environment variables from the .env file
load_dotenv()

# Gets the MongoDB connection string from the environment
# Uses the local MongoDB server if one is not provided
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://localhost:27017"
)

# Creates the connection to MongoDB
client = MongoClient(MONGODB_URL)

# Selects the database used for the notice board
database = client["notice_board"]

# Selects the collection where all notices will be stored
notices_collection = database["notices"]