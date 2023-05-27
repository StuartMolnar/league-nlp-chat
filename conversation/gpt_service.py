import os
from dotenv import load_dotenv
import openai
import yaml
import logging
import logging.config
import requests
import urllib.parse

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
    def __init__(self, query):
        self.query = query
        self.reply = self.__retrieve_context()

    
    def __retrieve_context(self):
        """
        Retrieve the context from the database.
        """
        base_url = app_config['endpoints']['vector'] + 'search/'
        url = f'{base_url}?{self.query}'
        response = requests.get(url)
        data = response.json()
        # data = [value for item in data for key, value in item.items() if key != 'id']
        logger.info(data)
        return data




# You are a league of legends chat assistant. Treat all replies as if directed towards a league of legends playing asking question. A question and context will be provided, if the question cannot be answered with the context, let the user know you do not have enough information. Do not mention the word context or query.
    
    
