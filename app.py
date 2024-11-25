from flask import Flask, jsonify, request
from flask_cors import CORS
from services.openai_service import OpenAIService
from dotenv import load_dotenv
from utils.logger import setup_logger
import os

# Setup logger
logger = setup_logger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

app = Flask(__name__)

# Clean and validate origins from environment
allowed_origins = [
    origin.strip() 
    for origin in os.getenv('ALLOWED_ORIGINS', '').split(',') 
    if origin.strip()
]

# Add development origins if not in production
if os.getenv('FLASK_ENV') != 'production':
    dev_origins = ['http://localhost:3000', 'http://127.0.0.1:3000']
    allowed_origins.extend(dev_origins)
    logger.info(f"Added development origins: {dev_origins}")

if not allowed_origins:
    logger.error("ALLOWED_ORIGINS environment variable not set!")
    raise ValueError("ALLOWED_ORIGINS must be set in environment variables")

# Validate all origins are HTTPS
if any(not origin.startswith('https://') for origin in allowed_origins):
    logger.error("All origins must use HTTPS!")
    raise ValueError("All origins must use HTTPS")

logger.info(f"Configured allowed origins: {allowed_origins}")



cors = CORS(app, resources={
    r"/api/*": {
        "origins": allowed_origins,
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True,
        "max_age": 600
    }
})

openai_service = OpenAIService()

@app.after_request
def after_request(response):
    logger.debug("Adding CORS headers to response")
    # Explicitly add CORS headers to each response
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/')
def home():
    logger.info("Home endpoint accessed")
    return jsonify({"message": "Welcome to the API!"})

@app.route('/api/items', methods=['GET'])
def get_items():
    logger.info("Getting items list")
    # Dummy data for demonstration
    items = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"}
    ]
    return jsonify(items)

@app.route('/api/topicitems', methods=['POST'])
def get_topic_items():
    logger.info("Topic items endpoint accessed")
    body = request.get_json()
    
    if not body or 'topic' not in body:
        logger.warning("Request missing required 'topic' field")
        return jsonify({"error": "topic is required"}), 400

    topic = str(body['topic'])
    butnot = str(body.get('butnot', None))
    logger.info(f"Generating items for topic: {topic}, butnot: {butnot}")
    result = openai_service.generate_description(topic, butnot)
    
    if not result['success']:
        logger.error(f"Failed to generate description: {result['error']}")
        return jsonify({"error": result['error']}), 500
    
    logger.info("Successfully generated topic items")
    return jsonify({
        "topic": body['topic'],
        "items": result['description']
    }), 200


def test():
    logger.info("Test endpoint accessed")
    return jsonify({
        "message": "success"
    }), 200

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(debug=True) 