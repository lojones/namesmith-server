from typing import Dict, Any, Optional
from pymongo import MongoClient
from utils.logger import setup_logger
import os
from datetime import datetime, timezone
import hashlib
import json

logger = setup_logger(__name__)

class MongoDBService:
    def __init__(self):
        logger.info("Initializing MongoDBService")
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        self.client = MongoClient(mongodb_uri)
        self.db = self.client.namesmith
        self.query_response_collection = self.db.NS_QUERIES
        logger.info("MongoDB connection established")

    def _generate_hash(self, prompt: str) -> str:
        """
        Generate a consistent hash from prompt
        """
        return hashlib.sha256(prompt.strip().encode('utf-8')).hexdigest()

    def save_response(self, prompt: str, response: str) -> bool:
        """
        Save an AI response with its prompt and metadata
        """
        logger.info(f"Saving response to MongoDB for {prompt}")
        try:
            document = {
                "hash": self._generate_hash(prompt),
                "prompt": prompt,
                "response": response,
                "created_at": datetime.utcnow()
            }
            self.query_response_collection.update_one(
                {"hash": document["hash"]},
                {"$set": document},
                upsert=True
            )
            logger.info("Response saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving response to MongoDB: {e}", exc_info=True)
            return False

    def find_response(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Find a response by its prompt hash
        """
        hash_value = self._generate_hash(prompt)
        logger.info(f"Searching for response with hash: {hash_value}")
        try:
            result = self.query_response_collection.find_one({"hash": hash_value})
            if result:
                logger.info("Response found")
                # Remove MongoDB's _id field before returning
                result.pop('_id', None)
                return result
            logger.info("Response not found")
            return None
        except Exception as e:
            logger.error(f"Error finding response in MongoDB: {e}", exc_info=True)
            return None
        
    def log_query(self, prompt: str):
        """Log a query to the time series collection using the prompt hash"""
        try:
            prompt_hash = self._generate_hash(prompt)  # Reuse existing hash function
            self.db.NS_QUERY_LOG.insert_one({
                'timestamp': datetime.now(timezone.utc),
                'prompt_hash': prompt_hash
            })
        except Exception as e:
            logger.error(f"Failed to log query: {str(e)}")