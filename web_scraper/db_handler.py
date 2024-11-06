from db_conn import get_db_client

def push_to_database(video_data):
    # Inserts video data, including comments, into the MongoDB database.
    db = get_db_client()
    collection = db['comments']
    
    # Insert video title and comments as a new document
    document = {
        "title": video_data["title"],
        "comments": video_data["comments"]
    }
    
    try:
        collection.insert_one(document)
        print(f"[INFO] Successfully saved video '{video_data['title']}' and its comments to MongoDB.")
    except Exception as e:
        print(f"[ERROR] Failed to save data to MongoDB: {e}")
