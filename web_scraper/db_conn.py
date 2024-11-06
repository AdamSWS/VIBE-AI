import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve MongoDB credentials
username = os.getenv("MONGO_USERNAME")
password = os.getenv("MONGO_PASSWORD")
host = os.getenv("MONGO_HOST")
database_name = os.getenv("MONGO_DB")

# MongoDB connection URI
mongo_uri = f"mongodb+srv://{username}:{password}@{host}/{database_name}?retryWrites=true&w=majority"

# Function to get the MongoDB client
def get_db_client():
    client = MongoClient(mongo_uri)
    db = client['youtube_comments']
    return db