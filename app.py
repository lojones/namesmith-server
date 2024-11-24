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

# Enable CORS for all routes with additional headers
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, resources={
    r"/*": {
        "origins": allowed_origins,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 600  # Cache preflight requests for 10 minutes
    }
})
logger.info(f"CORS enabled for origins: {allowed_origins}")

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