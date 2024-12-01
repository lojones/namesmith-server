from openai import OpenAI
from typing import Dict, Any
import os
import json
from utils.logger import setup_logger
from ast import literal_eval
from services.mongodb_service import MongoDBService

logger = setup_logger(__name__)

class OpenAIService:
    def __init__(self):
        logger.info("Initializing OpenAIService")
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not os.getenv('OPENAI_API_KEY'):
            logger.warning("OPENAI_API_KEY not found in environment variables")
        self.mongodb_service = MongoDBService()

    def generate_system_prompt(self) -> str:
        return "You are a helpful assistant that generates lists of names and \
                descriptions of things from a given topic.  Follow these guidelines: \n\
                * You always create a list of 20 names and descriptions.\n  \
                * The name should always be a single word.  \n \
                * The description should be have 2 parts: \n\
                    The first part is a short description about what it is in the context of the topic with no unnecessary adjectives. \
                    The second part is another short sentence that describes objective attributes of the item with no unnecessary adjectives, this sentence should be useful if I wanted to use this item to describe something else.  \
                        Here's an example: \
                            Orion - A prominent constellation containing some very bright stars.  It's a collection of things of different sizes.  \
                        Another example is: \
                            Vega - One of the brightest stars we can see.  It's large and bright.\n \
                * The description should be no more than 2 sentences and each sentence should be short and concise with no extra words or unneccesary adjectives. \n \
                * There should never be a single or double quote in any of the names or descriptions. \n \
                Your output should be a JSON object that follows this schema, \
                it should not have any markdown: \
                [{\"name\": \"name1\", \"desc\": \"description1\"}, {\"name\": \"name2\", \"desc\": \
                \"description2\"}, ...]"

    def generate_prompt(self, topic: str, butnot: str = None) -> str:
        if butnot:
            return f"Generate a JSON list of names and descriptions for things in this topic: {topic} \
                but not any of these items: {butnot}"
        else:
            return f"Generate a JSON list of names and descriptions for things in this topic: {topic}"

    def generate_description(self, topic: str, butnot: str = None) -> Dict[str, Any]:
        logger.info(f"Generating description for topic: {topic}")
        user_prompt = self.generate_prompt(topic, butnot)
        system_prompt = self.generate_system_prompt()
        # Check cache first
        cached_result = self.mongodb_service.find_response(user_prompt)
        if cached_result:
            logger.info(f"Found cached result for prompt: {topic} - Returning cached result")
            self.mongodb_service.log_query(user_prompt)
            return {
                "success": True,
                "description": cached_result['response'],
                "source": "cache"
            }
        # If not in cache, call OpenAI
        logger.info(f"Topic: {topic} - Not found in cache - Calling OpenAI")
        try:
            logger.info(f"Making OpenAI API call to OpenAI for {topic}")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                max_tokens=1000
            )
            try:
                logger.info(f"Parsing OpenAI response for {topic}")
                content = response.choices[0].message.content
                logger.debug(f"OpenAI response: {content}")
                parsed_content = literal_eval(content)
                
                # Save to cache
                self.mongodb_service.save_response(user_prompt, parsed_content)
                self.mongodb_service.log_query(user_prompt)
                
                logger.info(f"OpenAI success for {topic}")
                return {
                    "success": True,
                    "description": parsed_content,
                    "source": "openai"
                }
            except (ValueError, SyntaxError) as e:
                logger.error(f"Failed to parse OpenAI response: {e}")
                return {
                    "success": False,
                    "error": "Invalid JSON response from OpenAI"
                }
            
        except Exception as e:
            logger.error(f"Error generating description: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            } 