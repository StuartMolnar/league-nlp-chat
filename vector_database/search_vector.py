import os
import openai
import pinecone
import yaml
import logging
import logging.config
from dotenv import load_dotenv
import requests
import re

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

load_dotenv()
openai.api_key = os.getenv("GPT_KEY")
pinecone.init(api_key=os.getenv("PINECONE_KEY"), environment="asia-northeast1-gcp")

index = pinecone.Index(pinecone.list_indexes()[0])

class SearchVector:
    def __init__(self, query):
        logger.debug(f"Creating SearchVector object with query: {query}")
        self.__query = query
        self.__query_embedding = self.__embed_query()
        self.reply = self.__get_top_reply()

    
    def __embed_query(self):
        logger.debug(f"Embedding query")
        embed_model = app_config['models']['embed_model']

        res = openai.Embedding.create(
            input=self.__query, engine=embed_model
        )
        return res["data"][0]["embedding"]

    def __query_namespace(self, namespace, num_replies):
        logger.debug(f"Querying namespace: {namespace}")
        reply = index.query(queries=[self.__query_embedding], top_k=num_replies, include_metadata=True, namespace=namespace)
        return reply['results'][0]['matches']
    
    
    def __get_top_reply(self):
        logger.debug(f"Getting top reply")
        namespaces = [('matchups', 1), ('guides', 1), ('winrates', 1), ('rune_descriptions', 1), ('top_runes', 1)]
        replies = [(self.__query_namespace(namespace, num_replies), namespace) for namespace, num_replies in namespaces]
        logger.info(f"replies: {replies}")

        top_reply = ({'score': 0}, "")
        for data, namespace in replies:
            for item in data:
                if item['score'] > top_reply[0]['score']:
                    top_reply = item, namespace
       
        reply, namespace = top_reply
        logger.info(f"top reply: {reply}")
        id = re.findall(r'\d+$', reply['id'])[0]
        request_url = f"http://localhost:8000/{namespace}/{id}"
        logger.info(f"request url: {request_url}")
        response = requests.get(request_url)
        logger.info(f"response: {response.json()}")

        return response.json()

# search = SearchVector("What runes should I take on Jax?")
# logger.info(f"search.reply: {search.reply}")
