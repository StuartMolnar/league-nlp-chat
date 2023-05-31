import os
from dotenv import load_dotenv
import openai
import yaml
import logging
import logging.config
import requests
from typing import Dict

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Load environment variables from the .env file
load_dotenv()

# Set up the OpenAI API client
openai.api_key = os.getenv("GPT_KEY")

class GPT_Service:
    """
    A service for interacting with the GPT-3 model.

    Attributes:
        query (str): The query to be processed by the GPT-3 model.
        context (str): The context retrieved from the database.
        reply (str): The response generated by the GPT-3 model.
    """
    def __init__(self, query: str):
        self.query = query
        self.context = self.__retrieve_context()
        self.reply = self.__generate_gpt_response()

    @staticmethod
    def __generate_string_from_replies(data: Dict) -> str:
        """
        Generate a string from the replies data.

        Args:
            data (dict): The data containing the replies.

        Returns:
            str: The generated string.
        """
        result = ""
        for item in data:
            for key, value in item.items():
                if key != 'id':
                    if isinstance(value, dict):
                        for _, nested_value in value.items():
                            result += str(nested_value) + " "
                    else:
                        result += str(value) + " "
        return result

    def __retrieve_context(self) -> str:
        """
        Retrieve the context from the database.

        Returns:
            str: The retrieved context.
        """
        base_url = app_config['endpoints']['vector'] + 'search/'
        url = f'{base_url}?{self.query}'
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to retrieve context for query {self.query}: {str(e)}")
            raise

        data = response.json()
        logger.info(data)
        return self.__generate_string_from_replies(data)
    
    def __generate_gpt_response(self) -> str:
        """
        Generate a response from the GPT-3 engine.

        Returns:
            str: The generated response.
        """
        messages = [
            {"role": "system", "content": "You are a league of legends chat assistant."},
            {"role": "user", "content": f"Here is a query: {self.query}"},
            {"role": "assistant", "content": f"Answer the query with only the context provided: {self.context}"}
        ]

        try:
            answer = openai.ChatCompletion.create(
                model=app_config['models']['gpt_model'],
                messages=messages,
                max_tokens=300
            )
        except Exception as e:
            logger.error(f"Failed to generate GPT-3 response for query {self.query}: {str(e)}")
            raise

        return answer["choices"][0]["message"]["content"]

