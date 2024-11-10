from deep_translator import GoogleTranslator
from langdetect import detect

# Initialize the Translator
translator = GoogleTranslator(source='auto', target='en')

def load_keywords(filepath='./data/keywords.txt'):
    with open(filepath, 'r') as file:
        keywords = {line.strip().lower() for line in file if line.strip()} 
    return keywords

def normalize(value, max_value):
    return value / max_value if max_value else 0

def calculate_adjusted_score(comments, keywords, weights, threshold):
    labeled_comments = []
    comments_cache = {}

    # Calculate the max likes for normalization
    max_likes = max((comment['like_count'] for comment in comments), default=1)

    # Scaling factors to reduce the chance of scores approaching 1
    likes_scaling_factor = 0.3
    keyword_scaling_factor = 0.5

    # Process each comment
    for comment in comments:
        original_text = comment['text'].strip()

        # Check if the comment is non-empty and has substantial content
        if len(original_text.split()) < 4 or not any(char.isalnum() for char in original_text):
            print(f"Skipping comment ID: {comment['comment_id']} (No substantial content)")
            continue

        # Check if comment has already been processed and cached
        if comment['comment_id'] in comments_cache:
            labeled_comments.append(comments_cache[comment['comment_id']])
            continue

        # Detect the language of the original comment
        try:
            detected_language = detect(original_text)
            print(f"[DEBUG] Detected language for comment ID {comment['comment_id']}: {detected_language}")
        except Exception as e:
            print(f"[ERROR] Language detection failed for comment ID {comment['comment_id']}: {e}")
            detected_language = 'unknown'

        # Proceed with translation only if the detected language is not English
        if detected_language != 'en' and detected_language != 'unknown':
            try:
                translated_text = translator.translate(original_text)
            except Exception as e:
                print(f"Translation failed for comment ID {comment['comment_id']}: {e}")
                translated_text = original_text
        else:
            translated_text = original_text

        # Normalize likes with a scaling factor
        normalized_likes = (comment['like_count'] / max_likes) * likes_scaling_factor if max_likes > 0 else 0

        # Find matching keywords using set intersection for speed
        matched_keywords = [word for word in keywords if word in translated_text.lower()]
        keyword_count = len(matched_keywords)
        keyword_score = keyword_count * keyword_scaling_factor

        # Calculate the final score based on weighted factors and adjustments
        final_score = (
            weights['likes'] * normalized_likes +
            weights['keywords'] * keyword_score
        )

        # Assign label based on threshold
        label = 1 if final_score >= threshold else 0

        # Prepare the labeled comment data
        labeled_comment = {
            'text': original_text,
            'likes': comment['like_count'],
            'label': label,
            'score': final_score,
            'matched_keywords': matched_keywords
        }

        # Cache the result to avoid reprocessing
        comments_cache[comment['comment_id']] = labeled_comment
        labeled_comments.append(labeled_comment)

    return labeled_comments
