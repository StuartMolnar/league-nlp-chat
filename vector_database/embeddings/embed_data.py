import os
import openai
import pinecone
import yaml
import logging
import logging.config
from dotenv import load_dotenv
from prepare_data import PrepareData
import datetime
import requests
import re

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

load_dotenv()
openai.api_key = os.getenv("GPT_KEY")
pinecone.init(api_key=os.getenv("PINECONE_KEY"), environment="asia-northeast1-gcp")

index = pinecone.Index(pinecone.list_indexes()[0])

def embed_data(data):
    def embed_item(item):
        embed_model = "text-embedding-ada-002"
        text, id = item

        res = openai.Embedding.create(
            input=text, engine=embed_model
        )
        return res["data"][0]["embedding"], id
    embeddings = [embed_item(item) for item in data]
    return embeddings


def prepare_embeddings(embeddings, structure_id_func):
    logger.debug(f'Preparing embeddings')
    return [structure_id_func(embedding, id) for embedding, id in embeddings]


def upload_embeddings(embeddings):
    index.upsert(embeddings)


data_prep = PrepareData()


def structure_matchup(embedding, id):
    date_string = datetime.datetime.now().strftime('%B %d')
    return (f"matchup_{date_string}_{id}", embedding)

def structure_guide(embedding, id):
    return (f"guide_{id}", embedding)

def structure_winrate(embedding, id):
    return (f"winrate_{id}", embedding)

def structure_rune_description(embedding, id):
    logger.debug(f'Embedding rune description: {id}')
    return (f"rune_description_{id}", embedding)
    
def structure_top_rune(embedding, id):
    return (f"top_rune_{id}", embedding)


# matchups = data_prep.prepare_matchups()
# guides = data_prep.prepare_guides()
# winrates = data_prep.prepare_winrates()
# top_runes = data_prep.prepare_top_runes()
# logger.debug(f'requesting rune description data')
# rune_descriptions = data_prep.prepare_rune_descriptions()
# # logger.debug(f'embedding rune description data')
# rune_description_embeddings = embed_data(rune_descriptions)
# # logger.debug(f'preparing rune description embeddings')
# # logger.debug(f'length of rune description embeddings: {len(rune_description_embeddings)}')
# rune_description_embeddings = prepare_embeddings(rune_description_embeddings, structure_rune_description)
# # logger.debug(f'uploading rune description embeddings')
# upload_embeddings(rune_description_embeddings)
# logger.debug(f"pinecone rune entries: {index.fetch(ids=['rune_description_0', 'rune_description_1'])}")

def embed_query(query):
    embed_model = "text-embedding-ada-002"

    res = openai.Embedding.create(
        input=query, engine=embed_model
    )
    return res["data"][0]["embedding"]

query = "what is aftershock?"
logger.info(f"query: {query}")
query_embedding = embed_query(query)
#logger.info(f"query embedding: {query_embedding}")



reply = index.query(queries=[query_embedding], top_k=1, include_metadata=True)
logger.info(f"pinecone semantic search reply: {reply}")

reply_id = re.findall(r'\d+$', reply['results'][0]['matches'][0]['id'])[0]
logger.info(f"reply id: {reply_id}")
response = requests.get(f"http://localhost:8000/rune_descriptions/{reply_id}")
logger.info(f"response: {response.json()}")


# for match in reply['results'][0]['matches']:
#     logger.info(f"pinecone result: {match['values']}")


# todo: test the vector search by hardcoding a question, then embedding it, then searching for the closest vector






# 410 matchups = $0.0085
# guides = $0.5948
# winrates = $0.0009
# rune descriptions = $0.0017
# top runes = $0.0020
