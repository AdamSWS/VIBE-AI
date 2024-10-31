import requests
import json

# Place YouTube Data API V3 here
# If you don't have one create a Google Developer account and go to this link and
# click Try This API: https://console.cloud.google.com/marketplace/product/google/youtube.googleapis.com?project=data-mining-440319
API_KEY = "Your_API_KEY"

# Searches for videos on YouTube based on a query
def search_videos(query, max_results=5):
    # Create the URL that the YouTube Data API will search
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults={max_results}&key={API_KEY}"
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        return response.json()['items']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Get comments for a specific video
def get_video_comments(video_id, max_results=100):
    comments = [] # Stores video comments
    next_page_token = None

    while True:
        url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults={max_results}&key={API_KEY}"

        if next_page_token:
            url += f"&pageToken={next_page_token}"

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            for item in data.get('items', []):
                comment_data = item['snippet']['topLevelComment']['snippet']
                comment = {
                    'comment_id': item['id'],
                    'video_id': video_id,
                    'author': comment_data['authorDisplayName'],
                    'text': comment_data['textDisplay'],
                    'like_count': comment_data['likeCount'],
                    'timestamp': comment_data['publishedAt'],
                }
                comments.append(comment)

            next_page_token = data.get('nextPageToken')

            if not next_page_token:
                break
        else:
            print(f"Error: {response.status_code} - {response.text}")
            break

    return comments

# Gets the stats for a specific video
def get_video_statistics(video_id):
    # Create the URL for the YouTube API to return statistics
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={API_KEY}"
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()['items']
        if data:
            video_data = data[0]
            statistics = {
                'video_id': video_id,
                'title': video_data['snippet']['title'],
                'description': video_data['snippet']['description'],
                'views': video_data['statistics']['viewCount'],
                'likes': video_data['statistics']['likeCount'],
                'published_at': video_data['snippet']['publishedAt'],
            }
            return statistics
    else:
        print(f"Error: {response.status_code} - {response.text}")
    return None

search_results = search_videos("pokemon", max_results=5)

if search_results:
    for result in search_results:
        video_id = result['id']['videoId']

        # Get video statistics
        stats = get_video_statistics(video_id)

        # Get video comments
        comments = get_video_comments(video_id)
else:
    print("No videos found.")


# Uncomment below code to see if you're API Key is working, should print a
# large amounts of JSON
# print(comments)
# print(stats)