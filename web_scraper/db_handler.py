def save_comments_batch(comments_batch, video_title, db):
    if not comments_batch:
        print("[DEBUG] No comments to save.")
        return
    
    collection = db['comments']
    
    document = {
        "title": video_title,
        "comments": comments_batch
    }

    try:
        result = collection.insert_one(document)
        if result.inserted_id:
            print(f"[INFO] Successfully saved {len(comments_batch)} comments for video '{video_title}' to MongoDB with ID: {result.inserted_id}")
        else:
            print("[ERROR] Document batch insertion failed without an exception.")
    except Exception as e:
        print(f"[ERROR] Failed to save comments to MongoDB: {e}")