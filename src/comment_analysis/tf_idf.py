from sklearn.feature_extraction.text import TfidfVectorizer
from html import unescape
import os
from db import get_db

# Step 1: Connect to MongoDB and retrieve the comments
def get_comments_from_db():
    comments_collection = get_db("comments")
    comments = []
     # Fetch only translated_text
    comments_cursor = comments_collection.find({}, {"comments.translated_text": 1})
    for document in comments_cursor:
        for comment in document.get("comments", []):
            translated_text = comment.get("translated_text", "")
            if translated_text:
                comments.append(unescape(translated_text))
    return comments

# Step 2: Load suggestions from suggestions.txt
def load_suggestions():
    suggestions = []
    suggestions_file_path = "./tf_idf/data/suggestions.txt" 
    if os.path.exists(suggestions_file_path):
        with open(suggestions_file_path, "r") as file:
            suggestions = [line.strip() for line in file if line.strip()]
    else:
        print(f"Error: {suggestions_file_path} not found.")
    return suggestions

# Step 3: Run TF-IDF Analysis
def run_tfidf_analysis(comments, suggestions):
    all_texts = comments + suggestions
    
    # Combine texts for vectorization
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    tfidf_comments = tfidf_matrix[:len(comments)]
    tfidf_suggestions = tfidf_matrix[len(comments):]

    comment_means = tfidf_comments.mean(axis=0).A1
    suggestion_means = tfidf_suggestions.mean(axis=0).A1
    diff_scores = suggestion_means - comment_means

    terms = vectorizer.get_feature_names_out()
    term_diff_scores = dict(zip(terms, diff_scores))

    # Save the TF-IDF results to tfidf_results.txt
    with open("./tf_idf/data/tfidf_results.txt", "w") as output_file:
        for term, score in term_diff_scores.items():
            output_file.write(f"{term}: {score}\n")

    print("TF-IDF results saved to tfidf_results.txt")
    return term_diff_scores

# Step 4: Define categories and labeling thresholds
categories = {
    "Video Production": {"video", "videos", "filming", "edit", "shoot", "equipment", "professional", "style", "film"},
    "Content Creation": {"create", "creative", "creating", "make", "channel", "tutorial", "storytelling", "projects"},
    "Engagement": {"audience", "engaging", "viewers", "consistent", "share", "explain", "quality"},
    "Optimization & Strategy": {"optimize", "process", "improve", "consistent", "balance", "manage", "effectively", "handle"}
}

# Adjusted thresholds for stricter categorization
high_threshold = 0.09    # Increase to be more exclusive for high relevance
moderate_threshold = 0.05  # Increase for moderate relevance

# Step 5: Categorize terms based on TF-IDF scores
def categorize_text(tfidf_scores, categories, high_threshold, moderate_threshold):
    categorized_texts = {"High Relevance": [], "Moderate Relevance": [], "Low Relevance": []}

    for term, score in tfidf_scores.items():
        term_categories = [cat for cat, words in categories.items() if term in words]
        
        if score >= high_threshold and len(term_categories) > 0:
            categorized_texts["High Relevance"].append((term, score, term_categories))
        elif moderate_threshold <= score < high_threshold and len(term_categories) == 1:
            categorized_texts["Moderate Relevance"].append((term, score, term_categories))
        else:
            categorized_texts["Low Relevance"].append((term, score, term_categories))
    
    return categorized_texts

# Step 6: Label each comment as a suggestion or not, and remove duplicates
def label_comments(comments, categorized_terms):
    is_suggestion = set()      # Strictly relevant suggestions
    maybe_suggestion = set()   # Potential suggestions
    not_suggestion = set()     # General comments

    # Extract terms for different relevance levels
    high_relevance_terms = {term for term, _, _ in categorized_terms["High Relevance"]}
    moderate_relevance_terms = {term for term, _, _ in categorized_terms["Moderate Relevance"]}

    for comment in comments:
        comment_words = set(comment.lower().split())

        # Categorize the comment based on word relevance
        if comment_words & high_relevance_terms:
            is_suggestion.add(f"Suggestion: {comment}")
        elif comment_words & moderate_relevance_terms:
            maybe_suggestion.add(f"Maybe Suggestion: {comment}")
        else:
            not_suggestion.add(f"Not a Suggestion: {comment}")
    
    # Save categorized comments to respective files
    with open("./tf_idf/data/is_suggestion.txt", "w") as output_file:
        for label in is_suggestion:
            output_file.write(f"{label}\n")

    with open("./tf_idf/data/maybe_suggestion.txt", "w") as output_file:
        for label in maybe_suggestion:
            output_file.write(f"{label}\n")

    with open("./tf_idf/data/not_suggestion.txt", "w") as output_file:
        for label in not_suggestion:
            output_file.write(f"{label}\n")

    print("Categorized suggestions saved to is_suggestion.txt, maybe_suggestion.txt, and not_suggestion.txt")

# Main function to run the analysis
if __name__ == "__main__":
    comments = get_comments_from_db()
    suggestions = load_suggestions()

    if comments and suggestions:
        # Run TF-IDF Analysis
        tfidf_scores = run_tfidf_analysis(comments, suggestions)
        top_tfidf_scores = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)[:100]

        # Print the top 100 scores
        print("Top 100 TF-IDF Scores:")
        for term, score in top_tfidf_scores:
            print(f"{term}: {score}")
        # Categorize terms based on TF-IDF results
        categorized_terms = categorize_text(tfidf_scores, categories, high_threshold, moderate_threshold)

        # Label each comment and save to respective files
        label_comments(comments, categorized_terms)
    else:
        print("Error: Missing comments or suggestions data.")
