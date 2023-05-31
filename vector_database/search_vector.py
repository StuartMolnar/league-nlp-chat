import os
import openai
import pinecone
import yaml
import logging
import logging.config
from dotenv import load_dotenv
from typing import List, Tuple, Dict, Any
import concurrent.futures
from concurrent.futures import Future
import requests
import re
from typing import List, Tuple, Dict, Any
from requests.exceptions import RequestException

MAX_REPLIES = 5
MIN_REPLIES = 1

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

load_dotenv()

openai.api_key = os.getenv("GPT_KEY")
if openai.api_key is None:
    logger.error("Missing environment variable: GPT_KEY")
    raise ValueError("Missing environment variable: GPT_KEY")

pinecone_key = os.getenv("PINECONE_KEY")
if pinecone_key is None:
    logger.error("Missing environment variable: PINECONE_KEY")
    raise ValueError("Missing environment variable: PINECONE_KEY")

pinecone.init(api_key=pinecone_key, environment="asia-northeast1-gcp")

index = pinecone.Index(pinecone.list_indexes()[0])

class SearchVector:
    """
    This class is responsible for processing a query to retrieve the best reply from a vector database.

    Attributes:
        reply (dict): the best matching result retrieved for the query.
    """
    def __init__(self, query: str):
        """
        Initializes the SearchVector instance and processes the given query.

        Args:
            query (str): the query to process and retrieve results for.
        """
        logger.info(f"Creating SearchVector object with query: {query}")
        self.__query = query
        try:
            self.__query_embedding = self.__embed_query()
            self.reply = self.__get_top_reply()
        except Exception as e:
            logger.error(f"Failed to initialize SearchVector object: {e}")
            raise e

    
    def __embed_query(self) -> List[float]:
        """
        Embeds the query using OpenAI's embedding engine.

        Returns:
            list: The embedded version of the query.
        """
        logger.debug(f"Embedding query")
        embed_model = app_config['models']['embed_model']

        try:
            res = openai.Embedding.create(
                input=self.__query, engine=embed_model
            )
            return res["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise e

    def __query_namespace(self, namespace: str, num_replies: int) -> List[Dict[str, Any]]:
        """
        Queries a specific namespace in the Pinecone vector database.

        Args:
            namespace (str): The name of the namespace to query.
            num_replies (int): The number of top matches to retrieve.

        Returns:
            list: The top matching results from the namespace.
        """
        logger.debug(f"Querying namespace: {namespace}")
        try:
            reply = index.query(queries=[self.__query_embedding], top_k=num_replies, include_metadata=True, namespace=namespace)
            return reply['results'][0]['matches']
        except Exception as e:
            logger.error(f"Failed to query namespace: {e}")
            raise e
    
    
    def __get_top_reply(self) -> List[Dict[str, Any]]:
        """
        Retrieves the best matching replies for the query from all queried namespaces.

        Returns:
            list: The best matching results and their respective namespaces.
        """
        logger.info("Getting top replies")
        namespaces = [('matchups', 1), ('guides', 1), ('winrates', 1), ('rune_descriptions', 1), ('top_runes', 1)]
        replies: List[Tuple[Dict[str, Any], str]] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_namespace: Dict[Future, str] = {executor.submit(self.__query_namespace, namespace, num_replies): namespace for namespace, num_replies in namespaces}
            for future in concurrent.futures.as_completed(future_to_namespace):
                namespace = future_to_namespace[future]
                try:
                    data = future.result()
                except Exception as exc:
                    logger.error(f"{namespace} generated an exception: {exc}")
                else:
                    if data and isinstance(data, list):
                        replies.append((data, namespace))
                        logger.info(f"Namespace {namespace} returned data")

        num_replies = app_config.get('configurations', {}).get('num_replies', 1)
        num_replies = max(MIN_REPLIES, min(num_replies, MAX_REPLIES)) if isinstance(num_replies, int) else MAX_REPLIES

        flat_replies = [(data, namespace) for reply_data, namespace in replies for data in reply_data]        
        top_replies = sorted(flat_replies, key=lambda x: x[0].get('score', 0), reverse=True)[:num_replies]

        results: List[Dict[str, Any]] = []
        for reply, namespace in top_replies:
            id_match = re.findall(r'\d+$', reply.get('id', ''))
            if id_match:
                id = id_match[0]
                request_url = f"http://localhost:8000/{namespace}/{id}"
                try:
                    response = requests.get(request_url)
                    response.raise_for_status()
                    results.append(response.json())
                except requests.exceptions.HTTPError as errh:
                    logger.error(f"HTTP Error occurred: {errh}")
                except requests.exceptions.ConnectionError as errc:
                    logger.error(f"Error Connecting: {errc}")
                except requests.exceptions.Timeout as errt:
                    logger.error(f"Timeout Error: {errt}")
                except requests.exceptions.RequestException as err:
                    logger.error(f"Something went wrong with the request: {err}")
        
        return results