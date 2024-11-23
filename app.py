import os
import cv2
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image
from io import BytesIO
from sklearn.metrics.pairwise import cosine_similarity
import requests
import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import speech_recognition as sr

# Download necessary NLTK data
import nltk
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
CORS(app)

# Load the products CSV and orders data
products_df = pd.read_csv('data/amazon-products.csv')
orders_df = pd.read_excel('data/orders_data.xlsx')

# Directory where images are downloaded
image_dir = "data/downloaded_images"

# Ensure image directory exists
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# Function to clean the data before sending to the frontend
def cleanData(data):
    cleaned_data = []
    for item in data:
        cleaned_item = {key: (None if pd.isna(value) else value) for key, value in item.items()}
        cleaned_data.append(cleaned_item)
    return cleaned_data

# Function to download image from URL
def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
    else:
        print(f"Failed to download image: {url}")

# Function to resize images to a consistent size
def resize_image(image_path, size=(224, 224)):
    image = Image.open(image_path)
    return image.resize(size)

# Function to extract features from an image using ORB
def extract_features(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Failed to load image at {image_path}")
    orb = cv2.ORB_create()
    keypoints, descriptors = orb.detectAndCompute(image, None)
    return descriptors

# Function to compute similarity between two images
def compare_images(image_path1, image_path2):
    img1 = cv2.imread(image_path1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image_path2, cv2.IMREAD_GRAYSCALE)

    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)

    if des1 is None or des2 is None:
        return 0

    index_params = dict(algorithm=6, table_number=6, key_size=12, multi_probe_level=1)
    search_params = dict(checks=50)

    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:  # Ensure there are at least two matches to unpack
            m, n = match_pair
            if m.distance < 0.7 * n.distance:
                good_matches.append(m)

    return len(good_matches)

# Sentiment analysis using VADER
sid = SentimentIntensityAnalyzer()

def compute_sentiment_score(review_text):
    if isinstance(review_text, str) and review_text.strip():
        # Split the reviews if there are multiple, separated by commas
        reviews = review_text.split(",") if "," in review_text else [review_text]
        
        # Calculate sentiment for each review
        sentiment_scores = [sid.polarity_scores(review)['compound'] for review in reviews]
        
        # Calculate the average sentiment score
        average_sentiment_score = np.mean(sentiment_scores)
        return average_sentiment_score
    else:
        return 0.0  # Return a neutral sentiment score for invalid or empty text


# Preprocess text (remove stopwords, tokenize, and lower case)
def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words and word.isalnum()]
    return tokens

# Function to handle missing or invalid image URLs
def get_image_url(image_url):
    if pd.isna(image_url) or not re.match(r'^https?:\/\/.*\.(jpg|jpeg|png|webp)$', image_url):
        return 'default_image.jpg'  # A placeholder image URL if invalid or NaN
    return image_url




# Route to handle image search
@app.route('/api/image-search', methods=['POST'])
def image_search():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    img = Image.open(file.stream)
    img.save("temp_image.jpg")

    matched_products = []

    # Compare uploaded image with all downloaded product images
    for index, row in products_df.iterrows():
        product_image_name = f"{row['title'][:50].replace(' ', '_')}.jpg"
        product_image_path = os.path.join(image_dir, product_image_name)
        
        if not os.path.exists(product_image_path):
            continue
        
        similarity = compare_images("temp_image.jpg", product_image_path)

        if similarity > 50:  # Threshold can be adjusted
            matched_products.append({
                'title': row['title'],
                'url': row['url'],
                'initial_price':row['initial_price'],
                'top_review': row['top_review'],
                'image_url': get_image_url(row['image_url']),  # Handle image URL errors
                'sentiment_score': row.get('sentiment_score', 0), 
                'similarity_score': similarity
            })

    matched_products = sorted(matched_products, key=lambda x: x['similarity_score'], reverse=True)

    if matched_products:
        return jsonify({'search_results': matched_products[:5]})
    
    return jsonify({'error': 'No matching products found'}), 404


# Route for voice-based product search
@app.route('/api/voice-search', methods=['POST'])
def voice_search():
    recognizer = sr.Recognizer()
    audio_file = request.files.get('audio')

    if not audio_file:
        return jsonify({'error': 'No audio file provided'}), 400

    # Convert the audio file to audio data
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)

    try:
        # Recognize speech using Google's web service
        query = recognizer.recognize_google(audio_data)
        return jsonify({'query': query})

    except sr.UnknownValueError:
        return jsonify({'error': 'Could not understand the audio'}), 400

    except sr.RequestError:
        return jsonify({'error': 'Error with the recognition service'}), 500

# Route to search for products based on the query
@app.route('/api/search', methods=['GET'])
def search_products():
    query = request.args.get('query', '').strip()

    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    # Preprocess the search query
    processed_query = preprocess_text(query)
    matched_products = []

    # Search for matching products based on query
    for index, row in products_df.iterrows():
        product_title = row['title']
        review_text = row['top_review']
        
        # Compute sentiment score
        sentiment_score = compute_sentiment_score(review_text)
        processed_title = preprocess_text(product_title)
        matching_tokens = set(processed_query).intersection(set(processed_title))
        match_score = len(matching_tokens)

        # Exact match check
        if query.lower() == product_title.lower():
            matched_products = [{
                'title': row['title'],
                'url': row['url'],
                'initial_price':row['initial_price'],
                'image_url': get_image_url(row['image_url']),  # Handle image URL errors
                'sentiment_score': sentiment_score,
                'match_score': match_score,
                'rating': row['rating'],
                'top_review': row['top_review'],
                'category': row['categories']
            }]
            break

        # Partial or keyword match check
        if match_score > 0 or re.search(r'\b' + re.escape(query.lower()) + r'\b', product_title.lower()):
            matched_products.append({
                'title': row['title'],
                'url': row['url'],
                'initial_price':row['initial_price'],
                'image_url': get_image_url(row['image_url']),  # Handle image URL errors
                'sentiment_score': sentiment_score,
                'match_score': match_score,
                'rating': row['rating'],
                'top_review': row['top_review'],
                'category': row['categories'],
            })

    # If only one product is found and it matches exactly
    if matched_products and len(matched_products) == 1 and matched_products[0]['title'].lower() == query.lower():
        return jsonify(matched_products)

    # Sort products by match score and sentiment score
    matched_products = sorted(matched_products, key=lambda x: (x['match_score'], x['sentiment_score']), reverse=True)

    if matched_products:
        # Extract the category from the first matched product
        top_category = matched_products[0].get('category', '')
        
        # Get product recommendations from the matched category, sorted by sentiment score
        category_recommendations = get_category_recommendations(top_category)

        return jsonify({
            'search_results': matched_products[:5],  # Top 5 search results
            'category_recommendations': category_recommendations  # Category-based recommendations
        })

    return jsonify({'error': 'No products found'}), 404
def get_category_recommendations(category):

    """Get recommended products from the same category, sorted by sentiment score"""

    category_recommendations = []

    

    # Find products in the same category as the search result

    for index, row in products_df.iterrows():

        product_category = row['categories']

        if category.lower() in product_category.lower():

            sentiment_score = compute_sentiment_score(row['top_review'])

            category_recommendations.append({

                'title': row['title'],

                'url': row['url'],
                'initial_price':row['initial_price'],

                'image_url': row['image_url'],

                'sentiment_score': sentiment_score,

                'rating': row['rating'],

                'category': row['categories']

            })



    # Sort recommendations by sentiment score (descending order)

    category_recommendations = sorted(category_recommendations, key=lambda x: x['sentiment_score'], reverse=True)



    return category_recommendations[:5]  # Return top 5 recommendations

# Route to check the status of an order
@app.route('/api/order-status', methods=['GET'])
def get_order_status():
    order_no = request.args.get('orderNo')  # Use 'orderNo' from the query parameter

    if not order_no:
        return jsonify({'error': 'Order ID is required'}), 400

    order_status = orders_df[orders_df['order_no'] == order_no]

    if not order_status.empty:
        order_details = order_status.iloc[0].to_dict()
        order_details = {key: (None if value is pd.NA or pd.isna(value) else value) for key, value in order_details.items()}
        return jsonify(order_details)
    else:
        return jsonify({'error': 'Order not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
