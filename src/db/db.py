import os
import hashlib
from pymongo import MongoClient

# Environment variables for MongoDB connection
username = os.getenv("MONGO_USERNAME")
password = os.getenv("MONGO_PASSWORD")
host = os.getenv("MONGO_HOST")
database_name = os.getenv("MONGO_DB")

mongo_uri = f"mongodb+srv://{username}:{password}@{host}/{database_name}?retryWrites=true&w=majority"

def get_db(collection_name):
    try:
        client = MongoClient(mongo_uri)
        db = client['youtube_comments']
        collection = db[collection_name]
        return collection, client
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        raise

def generate_hash(item):
    # Concatenate relevant fields
    item_string = f"{item['title']}{item['description']}"
    return hashlib.sha256(item_string.encode()).hexdigest()

def store_items_to_collection(collection_tuple_or_object, items):
    try:
        if isinstance(collection_tuple_or_object, tuple):
            collection = collection_tuple_or_object[0]
        else:
            collection = collection_tuple_or_object

        if isinstance(items, dict):
            items = [items]

        inserted_count = 0
        inserted_ids = []

        for item in items:
            # Prevent duplicates based on a unique hash
            item_hash = generate_hash(item)
            if collection.find_one({"_hash": item_hash}):
                print(f"[INFO] Duplicate detected: {item['title']}")
                continue

            item["_hash"] = item_hash
            result = collection.insert_one(item)
            inserted_count += 1
            inserted_ids.append(result.inserted_id)

        print(f"[INFO] Inserted {inserted_count} new items.")
        return {"inserted_count": inserted_count, "ids": inserted_ids}
    except Exception as e:
        print(f"[ERROR] Failed to insert items into collection: {e}")
        raise

def save_comments_batch(comments_batch, video_title, db=None):
    """
    Save a batch of comments with the video title to the MongoDB database.

    Parameters:
        comments_batch (list): List of comments to save.
        video_title (str): The title of the video.
    """
    if not comments_batch:
        print("[DEBUG] No comments to save.")
        return

    try:
        # Get the collection and database connection
        collection, client = get_db("tech_comments")
        
        # Prepare the document for insertion
        document = {
            "title": video_title,
            "comments": comments_batch
        }

        # Attempt to insert into the collection
        result = collection.insert_one(document)
        if result.inserted_id:
            print(f"[INFO] Successfully saved {len(comments_batch)} comments for video '{video_title}' to MongoDB with ID: {result.inserted_id}")
        else:
            print("[ERROR] Document batch insertion failed without an exception.")
    except Exception as e:
        print(f"[ERROR] Failed to save comments to MongoDB: {e}")
    finally:
        # Close the MongoDB client connection
        if 'client' in locals():
            client.close()
